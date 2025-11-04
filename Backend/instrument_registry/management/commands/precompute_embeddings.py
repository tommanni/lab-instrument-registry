from django.core.management.base import BaseCommand
from instrument_registry.models import Instrument
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from django.db import transaction
from django.db.models import Q

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

class Command(BaseCommand):
    help = 'Pre-computes and stores embeddings and translations for all instruments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of instruments to process in a single batch.'
        )
        # Might be useful for model update or data corruption
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-processing of all instruments, even if already processed.'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        force_reprocess = options['force']

        if force_reprocess:
            # Process all instruments
            self.stdout.write(self.style.WARNING('Forcing re-processing of all instruments.'))
            instruments_queryset = Instrument.objects.all()
        else:
            # Filter out instruments that have already been successfully processed
            instruments_queryset = Instrument.objects.filter(
                Q(tuotenimi_en__in=["", "Translation Failed"]) |
                Q(embedding_en__isnull=True)
            )
            self.stdout.write(self.style.SUCCESS('Processing only instruments that need translation/embedding.'))

        instruments = list(instruments_queryset)  # Fetch filtered instruments into memory
        total_instruments_to_process = len(instruments)
        
        # Create a cache for unique Finnish product names
        translation_cache = {}

        # Preload all instruments with valid translations/embeddings for fast lookup
        valid_instruments = Instrument.objects.filter(
            ~Q(tuotenimi_en__in=["", "Translation Failed"]),
            ~Q(embedding_en__isnull=True)
        ).only('tuotenimi', 'tuotenimi_en', 'embedding_en')
        tuotenimi_lookup = {instr.tuotenimi.lower(): instr for instr in valid_instruments}
        
        self.stdout.write(self.style.SUCCESS(
            f'Starting to process {total_instruments_to_process} instruments in batches of {batch_size}.'
        ))

        # Create session once for all HTTP requests
        session = requests_retry_session()

        for i in range(0, total_instruments_to_process, batch_size):
            batch = instruments[i:i + batch_size]
            batch_tuotenimi_map = {instrument.tuotenimi.lower(): instrument for instrument in batch}
            unique_tuotenimi_in_batch = list(batch_tuotenimi_map.keys())
            
            texts_to_process = []

            for tuotenimi in unique_tuotenimi_in_batch:
                # Check if translation and embeddings are already in cache
                if tuotenimi in translation_cache:
                    continue  # Already cached, will be applied below

                # Check preloaded instruments for existing valid data
                existing_instrument = tuotenimi_lookup.get(tuotenimi)
                if existing_instrument:
                    translated_text = existing_instrument.tuotenimi_en
                    embedding_en = existing_instrument.embedding_en
                    translation_cache[tuotenimi] = (translated_text, embedding_en)
                else:
                    texts_to_process.append(tuotenimi)
                    
            # Make batch request only for texts that truly need processing
            if texts_to_process:
                try:
                    response = session.post(
                        "http://semantic-search-service:8001/process_batch", 
                        json={"texts": texts_to_process},
                        timeout=30
                    )
                    response.raise_for_status()  # Raise an exception for bad status codes
                    
                    batch_results = response.json()
                    for text, result in zip(texts_to_process, batch_results):
                        translated_text = result['translated_text']
                        embedding_en = result['embedding_en']
                        translation_cache[text] = (translated_text, embedding_en)

                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(
                        f'Error connecting to semantic search service for batch: {e}'
                    ))
                    for text in texts_to_process:
                        translation_cache[text] = ("Translation Failed", None)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'An unexpected error occurred: {e}'
                    ))
                    for text in texts_to_process:
                        translation_cache[text] = ("Translation Failed", None)
            
            # Update instruments in batch
            instruments_to_update = []
            for instrument in batch:
                tuotenimi = instrument.tuotenimi.lower()
                translated_text, embedding_en = translation_cache.get(
                    tuotenimi, ("Translation Failed", None)
                )
                
                instrument.tuotenimi_en = translated_text
                instrument.embedding_en = embedding_en
                instruments_to_update.append(instrument)
            
            # Bulk update for the batch
            with transaction.atomic():
                Instrument.objects.bulk_update(
                    instruments_to_update, 
                    ['tuotenimi_en', 'embedding_en']
                )
                self.stdout.write(self.style.SUCCESS(
                    f'Batch {i//batch_size + 1}/{(total_instruments_to_process + batch_size - 1)//batch_size} processed and updated.'
                ))

        # Close session after all batches
        session.close()  

        self.stdout.write(self.style.SUCCESS('\nFinished processing all instruments.'))
        successful = Instrument.objects.exclude(
            tuotenimi_en__in=["", "Translation Failed"]
        ).count()
        failed = Instrument.objects.filter(
            tuotenimi_en="Translation Failed"
        ).count()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n=== Summary ===\n'
            f'Total processed: {total_instruments_to_process}\n'
            f'Successful: {successful}\n'
            f'Failed: {failed}\n'
            f'Unique translations: {len(translation_cache)}'
        )) 