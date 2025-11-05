from django.db import transaction
from django.db.models import Q

from instrument_registry.models import Instrument
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def _requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
):
    session = requests.Session()
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


def precompute_instrument_embeddings(
    *,
    batch_size: int = 100,
    force: bool = False,
    on_info=lambda msg: None,
    on_error=lambda msg: None,
) -> dict:
    """
    Shared helper that performs the actual embedding precomputation work.
    Returns a summary dict with totals so callers can display results.
    """
    if force:
        instruments_queryset = Instrument.objects.all()
        on_info('Forcing re-processing of all instruments.')
    else:
        instruments_queryset = Instrument.objects.filter(
            Q(tuotenimi_en__in=["", "Translation Failed"]) |
            Q(embedding_en__isnull=True)
        )
        on_info('Processing only instruments that need translation/embedding.')

    instruments = list(instruments_queryset)
    total_instruments_to_process = len(instruments)

    translation_cache = {}

    valid_instruments = Instrument.objects.filter(
        ~Q(tuotenimi_en__in=["", "Translation Failed"]),
        ~Q(embedding_en__isnull=True)
    ).only('tuotenimi', 'tuotenimi_en', 'embedding_en')
    tuotenimi_lookup = {instr.tuotenimi.lower(): instr for instr in valid_instruments}

    on_info(f'Starting to process {total_instruments_to_process} instruments in batches of {batch_size}.')

    session = _requests_retry_session()

    try:
        for i in range(0, total_instruments_to_process, batch_size):
            batch = instruments[i:i + batch_size]
            batch_tuotenimi_map = {instrument.tuotenimi.lower(): instrument for instrument in batch}
            unique_tuotenimi_in_batch = list(batch_tuotenimi_map.keys())

            texts_to_process = []

            for tuotenimi in unique_tuotenimi_in_batch:
                if tuotenimi in translation_cache:
                    continue

                existing_instrument = tuotenimi_lookup.get(tuotenimi)
                if existing_instrument:
                    translated_text = existing_instrument.tuotenimi_en
                    embedding_en = existing_instrument.embedding_en
                    translation_cache[tuotenimi] = (translated_text, embedding_en)
                else:
                    texts_to_process.append(tuotenimi)

            if texts_to_process:
                try:
                    response = session.post(
                        "http://semantic-search-service:8001/process_batch",
                        json={"texts": texts_to_process},
                        timeout=30
                    )
                    response.raise_for_status()

                    batch_results = response.json()
                    for text, result in zip(texts_to_process, batch_results):
                        translated_text = result['translated_text']
                        embedding_en = result['embedding_en']
                        translation_cache[text] = (translated_text, embedding_en)

                except requests.exceptions.RequestException as exc:
                    on_error(f'Error connecting to semantic search service for batch: {exc}')
                    for text in texts_to_process:
                        translation_cache[text] = ("Translation Failed", None)
                except Exception as exc:
                    on_error(f'An unexpected error occurred: {exc}')
                    for text in texts_to_process:
                        translation_cache[text] = ("Translation Failed", None)

            instruments_to_update = []
            for instrument in batch:
                tuotenimi = instrument.tuotenimi.lower()
                translated_text, embedding_en = translation_cache.get(
                    tuotenimi, ("Translation Failed", None)
                )

                should_update_translation = instrument.tuotenimi_en in ("", "Translation Failed")
                if should_update_translation:
                    instrument.tuotenimi_en = translated_text
                instrument.embedding_en = embedding_en
                instruments_to_update.append(instrument)

            with transaction.atomic():
                Instrument.objects.bulk_update(
                    instruments_to_update,
                    ['tuotenimi_en', 'embedding_en']
                )
                on_info(
                    f'Batch {i//batch_size + 1}/{(total_instruments_to_process + batch_size - 1)//batch_size} processed and updated.'
                )
    finally:
        session.close()

    # Recount success/failure based on cached results and updates performed
    successful = sum(
        1 for _tuotenimi, (_translated, embedding) in translation_cache.items()
        if embedding is not None
    )
    failed = len(translation_cache) - successful

    return {
        'processed_count': total_instruments_to_process,
        'successful': successful,
        'failed': failed,
        'cache_size': len(translation_cache),
    }
