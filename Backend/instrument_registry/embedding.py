from collections import Counter, defaultdict

from django.db import transaction
from django.db.models import Q
from django.conf import settings
from simple_history.utils import bulk_update_with_history

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
SERVICE_URL = getattr(settings, 'SEMANTIC_SERVICE_URL', 'http://semantic-search-service:8001')

def precompute_instrument_embeddings(
    *,
    batch_size: int = 100,
    force: bool = False,
    on_info=lambda msg: None,
    on_error=lambda msg: None,
) -> dict:
    """
    Shared helper that performs embedding and translation precomputation work.
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

    embedding_by_translation, name_translation_cache = _build_translation_and_embedding_caches()

    on_info(f'Starting to process {total_instruments_to_process} instruments in batches of {batch_size}.')

    session = _requests_retry_session()

    try:
        for i in range(0, total_instruments_to_process, batch_size):
            batch = instruments[i:i + batch_size]
            if not batch:
                continue

            batch_states, unique_names_to_translate = _collect_batch_state(
                batch,
                name_translation_cache,
                embedding_by_translation
            )

            if unique_names_to_translate:
                # translate missing names
                _translate_missing(
                    unique_names_to_translate,
                    session,
                    (name_translation_cache, embedding_by_translation),
                    on_error,
                )

            translations_needing_embedding = _resolve_translations_and_identify_missing_embeddings(
                batch_states,
                (name_translation_cache, embedding_by_translation)
            )

            _embed_missing(
                translations_needing_embedding,
                session,
                embedding_by_translation,
                on_error,
            )

            instruments_to_update = _build_instruments_to_update(
                batch_states,
                embedding_by_translation
            )

            with transaction.atomic(): # Either whole batch update succeeds or none of them do
                bulk_update_with_history(
                    instruments_to_update,
                    Instrument,
                    ['tuotenimi_en', 'embedding_en']
                )
                on_info(
                    f'Batch {i//batch_size + 1}/{(total_instruments_to_process + batch_size - 1)//batch_size} processed and updated.'
                )
    finally:
        session.close()

    successful = Instrument.objects.exclude(tuotenimi_en__in=["", "Translation Failed"]).count()
    failed = Instrument.objects.filter(tuotenimi_en="Translation Failed").count()

    return {
        'processed_count': total_instruments_to_process,
        'successful': successful,
        'failed': failed,
        'cache_size': len(name_translation_cache),
    }

def _build_translation_and_embedding_caches():
    """
    Builds a cache of translations and embeddings for each product name.
    """
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

    # Cache most common translation for each product name
    name_translation_cache = {
        key: counter.most_common(1)[0][0] for key, counter in name_translation_counts.items()
    }

    return embedding_by_translation, name_translation_cache

def _collect_batch_state(batch, name_translation_cache, embedding_by_translation):
    """
    Collects the state of each instrument in the batch.
    """
    batch_states = []
    unique_names_to_translate = {}

    for instrument in batch:
        name = instrument.tuotenimi or ""
        tuotenimi_key = name.lower()

        has_valid_translation = instrument.tuotenimi_en not in INVALID_TRANSLATION_VALUES
        desired_translation = instrument.tuotenimi_en if has_valid_translation else name_translation_cache.get(tuotenimi_key)

        if (
            not has_valid_translation
            and desired_translation is None
            and tuotenimi_key not in unique_names_to_translate
        ):
            unique_names_to_translate[tuotenimi_key] = instrument.tuotenimi

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

    return batch_states, unique_names_to_translate

def _build_instruments_to_update(batch_states, embedding_by_translation):
    """
    Builds the list of instruments to update.
    """
    instruments_to_update = []
    for state in batch_states:
        instrument = state['instrument']
        translation = state['desired_translation']

        if not state['has_valid_translation']:
            instrument.tuotenimi_en = translation or "Translation Failed"

        # If we still don't have the embedding in state, check the newly populated cache
        if (
            state['resolved_embedding'] is None and
            translation not in INVALID_TRANSLATION_VALUES
        ):
            state['resolved_embedding'] = embedding_by_translation.get(translation)

        if instrument.embedding_en is None and state['resolved_embedding'] is not None:
            instrument.embedding_en = state['resolved_embedding']

        instruments_to_update.append(instrument)
    return instruments_to_update

def _translate_missing(unique_names_to_translate, session, caches, on_error):
    """
    Translates missing names.
    """
    name_translation_cache, embedding_by_translation = caches

    # Translate every Finnish name still lacking a usable translation
    texts_to_process = list(unique_names_to_translate.values())
    keys_to_process = list(unique_names_to_translate.keys())

    try:
        response = session.post(
            f"{SERVICE_URL}/process_batch",
            json={"texts": texts_to_process},
            timeout=30
        )
        response.raise_for_status()

        batch_results = response.json()

        # Add processed batch results to translation cache
        for name, result in zip(keys_to_process, batch_results):
            translated_text = result['translated_text']
            embedding_en = result['embedding_en']

            name_translation_cache[name] = translated_text

            if translated_text not in INVALID_TRANSLATION_VALUES and embedding_en is not None:
                embedding_by_translation[translated_text] = embedding_en

    except requests.exceptions.RequestException as exc:
        on_error(f'Error connecting to semantic search service for batch: {exc}')
        for name in keys_to_process:
            name_translation_cache[name] = "Translation Failed"
    except Exception as exc:
        on_error(f'An unexpected error occurred: {exc}')
        for name in keys_to_process:
            name_translation_cache[name] = "Translation Failed"

def _resolve_translations_and_identify_missing_embeddings(batch_states, caches):
    """
    Resolves translations and identifies missing embeddings.
    """
    name_translation_cache, embedding_by_translation = caches

    translations_needing_embedding = set()
    for state in batch_states:
        # Resolve translation from cache if missing
        if state['desired_translation'] is None:
            state['desired_translation'] = name_translation_cache.get(
                state['tuotenimi_key'],
                "Translation Failed"
            )
        # Check if embedding is available in cache
        if (
            state['resolved_embedding'] is None and
            state['desired_translation'] not in INVALID_TRANSLATION_VALUES
        ):
            # Try to get it from local dict
            cached_embedding = embedding_by_translation.get(state['desired_translation'])

            if cached_embedding is not None:
                state['resolved_embedding'] = cached_embedding
            else:
                # Mark for fetching
                translations_needing_embedding.add(state['desired_translation'])

    return translations_needing_embedding

def _embed_missing(translations_needing_embedding, session, embedding_by_translation, on_error):
    """
    Embeds missing translations.
    """

    texts_to_embed = list(translations_needing_embedding)
    if texts_to_embed:
        try:
            response = session.post(
                f"{SERVICE_URL}/embed_en_batch",
                json={"texts": texts_to_embed},
                timeout=30
            )
            response.raise_for_status()

            embeddings_result = response.json().get('embeddings', [])

            # Map results back to the cache
            for text, embedding in zip(texts_to_embed, embeddings_result, strict=True):
                embedding_by_translation[text] = embedding

        except requests.exceptions.RequestException as exc:
            on_error(f'Error connecting to batch embedding service: {exc}')
            # Mark all as failed so we don't crash later logic
            for text in texts_to_embed:
                embedding_by_translation[text] = None

        except Exception as exc:
            on_error(f'Unexpected error during batch embedding: {exc}')
            for text in texts_to_embed:
                embedding_by_translation[text] = None
