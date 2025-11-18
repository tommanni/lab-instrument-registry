from collections import Counter, defaultdict

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


INVALID_TRANSLATION_VALUES = {"", "Translation Failed"}


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

    instruments = list(instruments_queryset) # Fetch instruments into memory
    total_instruments_to_process = len(instruments)

    name_translation_counts = defaultdict(Counter)
    embedding_by_translation = {}

    # Build a per-name translation majority and cache any known embeddings per translation.
    existing_translations = Instrument.objects.exclude(
        tuotenimi_en__in=INVALID_TRANSLATION_VALUES
    ).only('tuotenimi', 'tuotenimi_en', 'embedding_en')

    for instrument in existing_translations:
        tuotenimi_key = instrument.tuotenimi.lower()
        translation_value = instrument.tuotenimi_en
        name_translation_counts[tuotenimi_key][translation_value] += 1
        if instrument.embedding_en is not None and translation_value not in embedding_by_translation:
            embedding_by_translation[translation_value] = instrument.embedding_en

    name_translation_cache = {
        key: counter.most_common(1)[0][0] for key, counter in name_translation_counts.items()
    }

    on_info(f'Starting to process {total_instruments_to_process} instruments in batches of {batch_size}.')

    session = _requests_retry_session()

    try:
        for i in range(0, total_instruments_to_process, batch_size):
            batch = instruments[i:i + batch_size]
            if not batch:
                continue

            batch_states = []
            names_to_translate = []
            names_to_translate_set = set()
            original_tuotenimi_by_key = {}

            for instrument in batch:
                tuotenimi_key = instrument.tuotenimi.lower()
                original_tuotenimi_by_key.setdefault(tuotenimi_key, instrument.tuotenimi)

                has_valid_translation = instrument.tuotenimi_en not in INVALID_TRANSLATION_VALUES
                desired_translation = instrument.tuotenimi_en if has_valid_translation else name_translation_cache.get(tuotenimi_key)

                if not has_valid_translation and desired_translation is None and tuotenimi_key not in names_to_translate_set:
                    names_to_translate.append(tuotenimi_key)
                    names_to_translate_set.add(tuotenimi_key)

                resolved_embedding = instrument.embedding_en
                if resolved_embedding is None and desired_translation:
                    resolved_embedding = embedding_by_translation.get(desired_translation)

                batch_states.append({
                    'instrument': instrument,
                    'tuotenimi_key': tuotenimi_key,
                    'has_valid_translation': has_valid_translation,
                    'desired_translation': desired_translation,
                    'resolved_embedding': resolved_embedding,
                })

            if names_to_translate:
                # Translate every Finnish name still lacking a usable translation.
                texts_to_process = [original_tuotenimi_by_key[name] for name in names_to_translate]
                try:
                    response = session.post(
                        "http://semantic-search-service:8001/process_batch",
                        json={"texts": texts_to_process},
                        timeout=30
                    )
                    response.raise_for_status()

                    # Add processed batch results to translation cache
                    batch_results = response.json()
                    for name, result in zip(names_to_translate, batch_results):
                        translated_text = result['translated_text']
                        embedding_en = result['embedding_en']
                        name_translation_cache[name] = translated_text
                        if translated_text not in INVALID_TRANSLATION_VALUES and embedding_en is not None:
                            embedding_by_translation[translated_text] = embedding_en
                except requests.exceptions.RequestException as exc:
                    on_error(f'Error connecting to semantic search service for batch: {exc}')
                    for name in names_to_translate:
                        name_translation_cache[name] = "Translation Failed"
                except Exception as exc:
                    on_error(f'An unexpected error occurred: {exc}')
                    for name in names_to_translate:
                        name_translation_cache[name] = "Translation Failed"

            for state in batch_states:
                if state['desired_translation'] is None:
                    state['desired_translation'] = name_translation_cache.get(
                        state['tuotenimi_key'],
                        "Translation Failed"
                    )
                if (
                    state['resolved_embedding'] is None and
                    state['desired_translation'] not in INVALID_TRANSLATION_VALUES
                ):
                    state['resolved_embedding'] = embedding_by_translation.get(
                        state['desired_translation']
                    )

            # For reused translations that still have no embedding, fetch a fresh vector.
            translations_needing_embedding = {
                state['desired_translation']
                for state in batch_states
                if state['desired_translation'] not in INVALID_TRANSLATION_VALUES
                and state['resolved_embedding'] is None
            }

            for translation_text in translations_needing_embedding:
                try:
                    response = session.post(
                        "http://semantic-search-service:8001/embed_en",
                        json={"text": translation_text},
                        timeout=30
                    )
                    response.raise_for_status()
                    embedding_result = response.json().get('embedding')
                    embedding_by_translation[translation_text] = embedding_result
                except requests.exceptions.RequestException as exc:
                    on_error(f'Error connecting to semantic search service for embedding: {exc}')
                    embedding_by_translation[translation_text] = None
                except Exception as exc:
                    on_error(f'An unexpected error occurred while embedding text: {exc}')
                    embedding_by_translation[translation_text] = None

            for state in batch_states:
                if (
                    state['resolved_embedding'] is None and
                    state['desired_translation'] not in INVALID_TRANSLATION_VALUES
                ):
                    state['resolved_embedding'] = embedding_by_translation.get(
                        state['desired_translation']
                    )

            # Build the list of instruments for bulk update
            instruments_to_update = []
            for state in batch_states:
                instrument = state['instrument']
                final_translation = state['desired_translation'] or "Translation Failed"

                if not state['has_valid_translation']:
                    instrument.tuotenimi_en = final_translation

                if instrument.embedding_en is None and state['resolved_embedding'] is not None:
                    instrument.embedding_en = state['resolved_embedding']

                instruments_to_update.append(instrument)

            with transaction.atomic(): # Either whole batch update succeeds or none of them do
                Instrument.objects.bulk_update(
                    instruments_to_update,
                    ['tuotenimi_en', 'embedding_en']
                )
                on_info(
                    f'Batch {i//batch_size + 1}/{(total_instruments_to_process + batch_size - 1)//batch_size} processed and updated.'
                )
    finally:
        session.close()

    successful = Instrument.objects.exclude(
        tuotenimi_en__in=["", "Translation Failed"]
    ).count()
    failed = Instrument.objects.filter(
        tuotenimi_en="Translation Failed"
    ).count()

    return {
        'processed_count': total_instruments_to_process,
        'successful': successful,
        'failed': failed,
        'cache_size': len(name_translation_cache),
    }
