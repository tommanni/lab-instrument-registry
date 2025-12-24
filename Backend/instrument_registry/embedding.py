"""
Instrument Translation and Embedding Pipeline

Handles automated translation of instrument names (Finnish → English) and generates
semantic embeddings for search. Supports multiple valid translations per Finnish name
through majority voting.

KEY DESIGN:
- Never overwrites existing valid translations
- Uses majority voting when multiple translations exist for the same Finnish name
- Caches translations and embeddings to minimize API calls
- Processes instruments in batches for efficiency
- Marks failures as "Translation Failed" or None to prevent infinite retries
"""

from collections import Counter, defaultdict
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q
from django.conf import settings
from simple_history.utils import bulk_update_with_history

from instrument_registry.models import Instrument
from instrument_registry.enrichment import (
    enrich_instruments_batch, 
    INVALID_ENRICHMENT_VALUES
)
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

@dataclass
class InstrumentState:
    instrument: Instrument
    name_key: str
    has_valid_translation: bool
    has_valid_enrichment: bool
    resolved_enrichment: str | None
    resolved_translation: str | None
    resolved_embedding: list | None

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


# Translation values that indicate a missing or failed translation
INVALID_TRANSLATION_VALUES = {"", "Translation Failed"}

SERVICE_URL = getattr(settings, 'SEMANTIC_SERVICE_URL', 'http://semantic-search-service:8001')

def precompute_instrument_embeddings(
    *,
    batch_size: int = 100,
    force: bool = False,
    on_info=lambda msg: None,
    on_error=lambda msg: None,
    skip_enrichment: bool = False,
):
    """Precomputes translations and embeddings for instruments. Returns summary dict."""
    if force:
        instruments_queryset = Instrument.objects.all()
        on_info('Forcing re-processing of all instruments.')
    else:
        if skip_enrichment:
            instruments_queryset = Instrument.objects.filter(
                Q(tuotenimi_en__in=["", "Translation Failed"]) |
                Q(embedding_en__isnull=True)
            )
            on_info('Processing only instruments that need translation/embedding.')
        else:
            instruments_queryset = Instrument.objects.filter(
                Q(tuotenimi_en__in=["", "Translation Failed"]) |
                Q(enriched_description__isnull=True) |
                Q(embedding_en__isnull=True)
            )
            on_info('Processing instruments that need translation/enrichment/embedding.')
        

    instruments = list(instruments_queryset)
    total_instruments_to_process = len(instruments)

    embedding_by_translation, name_translation_cache = _build_translation_and_embedding_caches()

    on_info(f'Starting to process {total_instruments_to_process} instruments in batches of {batch_size}.')

    session = _requests_retry_session()

    try:
        for i in range(0, total_instruments_to_process, batch_size):
            batch = instruments[i:i + batch_size]
            if not batch:
                continue

            instruments_to_update = _process_batch(
                batch, 
                session, 
                (name_translation_cache, embedding_by_translation), 
                on_error
            )

            with transaction.atomic():
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
    Builds in-memory caches from existing database records to minimize API calls.
    Uses majority voting because multiple translations can exist for the same Finnish name.
    """
    name_translation_counts = defaultdict(Counter)
    embedding_by_translation = {}

    existing_translations = Instrument.objects.exclude(
        tuotenimi_en__in=INVALID_TRANSLATION_VALUES
    ).only('tuotenimi', 'tuotenimi_en', 'embedding_en')

    for instrument in existing_translations:
        name_key = instrument.tuotenimi.lower()
        translation_value = instrument.tuotenimi_en
        name_translation_counts[name_key][translation_value] += 1
        if instrument.embedding_en is not None and translation_value not in embedding_by_translation:
            embedding_by_translation[translation_value] = instrument.embedding_en

    name_translation_cache = {
        key: counter.most_common(1)[0][0] for key, counter in name_translation_counts.items()
    }

    return embedding_by_translation, name_translation_cache

def _process_batch(batch, session, caches, on_error):
    """Processes batch by translating missing names and generating embeddings."""
    name_translation_cache, embedding_by_translation = caches

    # Step 1: Analyze what each instrument needs (translation, embedding, or both)
    instrument_states, unique_names_to_translate = _collect_instrument_states(
        batch,
        name_translation_cache,
        embedding_by_translation
    )

    # Step 2: Translate any Finnish names not in cache via API
    if unique_names_to_translate:
        _translate_missing(
            unique_names_to_translate,
            session,
            (name_translation_cache, embedding_by_translation),
            on_error,
        )

    # Step 3: Update instrument_states with new translations and identify which need embeddings
    translations_needing_embedding = _resolve_translations_and_identify_missing_embeddings(
        instrument_states,
        (name_translation_cache, embedding_by_translation)
    )

    # Step 4: Generate embeddings for English translations not in cache
    _embed_missing(
        translations_needing_embedding,
        session,
        embedding_by_translation,
        on_error,
    )

    # Step 5: Prepare instruments with final translations and embeddings
    instruments_to_update = _build_instruments_to_update(
        instrument_states,
        embedding_by_translation
    )

    return instruments_to_update

def _collect_instrument_states(batch, name_translation_cache, embedding_by_translation):
    """
    Analyzes batch to determine what processing each instrument needs.
    
    Note: Existing valid translations are never overwritten, supporting multiple 
    valid translations for the same Finnish name.
    """
    instrument_states = []
    unique_names_to_translate = {}

    for instrument in batch:
        name = instrument.tuotenimi or ""
        name_key = name.lower()

        has_valid_translation = instrument.tuotenimi_en not in INVALID_TRANSLATION_VALUES
        resolved_translation = instrument.tuotenimi_en if has_valid_translation else name_translation_cache.get(name_key)

        if (
            not has_valid_translation
            and resolved_translation is None
            and name_key not in unique_names_to_translate
        ):
            unique_names_to_translate[name_key] = instrument.tuotenimi

        resolved_embedding = instrument.embedding_en
        if resolved_embedding is None and resolved_translation:
            resolved_embedding = embedding_by_translation.get(resolved_translation)

        instrument_states.append(
            InstrumentState(
                instrument=instrument,
                name_key=name_key,
                has_valid_translation=has_valid_translation,
                resolved_translation=resolved_translation,
                resolved_embedding=resolved_embedding,
            )
        )

    return instrument_states, unique_names_to_translate

def _translate_missing(unique_names_to_translate, session, caches, on_error):
    """
    Translates Finnish names to English via /process_batch endpoint.
    Updates both translation and embedding caches. Marks failures as "Translation Failed".
    """
    name_translation_cache, embedding_by_translation = caches

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

def _resolve_translations_and_identify_missing_embeddings(instrument_states, caches):
    """
    Updates instrument states with newly cached translations and identifies which 
    translations still need embeddings generated.
    """
    name_translation_cache, embedding_by_translation = caches

    translations_needing_embedding = set()
    for state in instrument_states:
        if state.resolved_translation is None:
            state.resolved_translation = name_translation_cache.get(
                state.name_key,
                "Translation Failed"
            )
        if (
            state.resolved_embedding is None and
            state.resolved_translation not in INVALID_TRANSLATION_VALUES
        ):
            cached_embedding = embedding_by_translation.get(state.resolved_translation)

            if cached_embedding is not None:
                state.resolved_embedding = cached_embedding
            else:
                translations_needing_embedding.add(state.resolved_translation)

    return translations_needing_embedding

def _embed_missing(translations_needing_embedding, session, embedding_by_translation, on_error):
    """
    Generates embeddings for English translations via /embed_en_batch endpoint.
    On error, sets embeddings to None (graceful degradation).
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

            for text, embedding in zip(texts_to_embed, embeddings_result, strict=True):
                embedding_by_translation[text] = embedding

        except requests.exceptions.RequestException as exc:
            on_error(f'Error connecting to batch embedding service: {exc}')
            for text in texts_to_embed:
                embedding_by_translation[text] = None

        except Exception as exc:
            on_error(f'Unexpected error during batch embedding: {exc}')
            for text in texts_to_embed:
                embedding_by_translation[text] = None

def _build_instruments_to_update(instrument_states, embedding_by_translation):
    """
    Applies final translations and embeddings to instruments for database update.
    """
    instruments_to_update = []
    for state in instrument_states:
        instrument = state.instrument
        translation = state.resolved_translation

        if not state.has_valid_translation:
            instrument.tuotenimi_en = translation or "Translation Failed"

        if (
            state.resolved_embedding is None and
            translation not in INVALID_TRANSLATION_VALUES
        ):
            state.resolved_embedding = embedding_by_translation.get(translation)

        if instrument.embedding_en is None and state.resolved_embedding is not None:
            instrument.embedding_en = state.resolved_embedding

        instruments_to_update.append(instrument)
    return instruments_to_update
