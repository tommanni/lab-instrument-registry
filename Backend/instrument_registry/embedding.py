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
    cache_key: str
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

def _get_cache_key(instrument):
    """
    Creates a composite key from Name + Model Info.
    This ensures that 'Analysaattori (Model A)' is treated differently 
    from 'Analysaattori (Model B)'.
    """
    name = (instrument.tuotenimi or "").strip().lower()
    
    brand_info = (instrument.merkki_ja_malli or "").strip().lower()
    
    return f"{name}|{brand_info}"

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
                Q(enriched_description__in=INVALID_ENRICHMENT_VALUES) |
                Q(embedding_en__isnull=True)
            )
            on_info('Processing instruments that need translation/enrichment/embedding.')
        

    instruments = list(instruments_queryset)
    total_instruments_to_process = len(instruments)

    translation_cache, enrichment_cache, embedding_cache = _build_caches()

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
                skip_enrichment,
                (translation_cache, enrichment_cache, embedding_cache), 
                on_error
            )

            with transaction.atomic():
                bulk_update_with_history(
                    instruments_to_update,
                    Instrument,
                    ['tuotenimi_en', 'enriched_description', 'embedding_en']
                )
                on_info(
                    f'Batch {i//batch_size + 1}/{(total_instruments_to_process + batch_size - 1)//batch_size} processed and updated.'
                )
    finally:
        session.close()

    successful = Instrument.objects.exclude(
        Q(tuotenimi_en__in=["", "Translation Failed"]) |
        Q(enriched_description__in=INVALID_ENRICHMENT_VALUES) |
        Q(embedding_en__isnull=True)
    ).count()
    failed = Instrument.objects.filter(
        Q(tuotenimi_en__in=["", "Translation Failed"]) |
        Q(enriched_description__in=INVALID_ENRICHMENT_VALUES) |
        Q(embedding_en__isnull=True)
    ).count()

    return {
        'processed_count': total_instruments_to_process,
        'successful': successful,
        'failed': failed,
        'cache_size': len(translation_cache),
    }

def _build_caches():
    """
    Builds in-memory caches from existing database records to minimize API calls.
    Uses majority voting because multiple translations can exist for the same Finnish name.
    """
    key_translation_counts = defaultdict(Counter)
    embedding_cache = {}
    enrichment_cache = {}

    existing_translations = Instrument.objects.exclude(
        tuotenimi_en__in=INVALID_TRANSLATION_VALUES
    ).only('tuotenimi', 'merkki_ja_malli', 'tuotenimi_en')

    for instrument in existing_translations:
        key = _get_cache_key(instrument)
        key_translation_counts[key][instrument.tuotenimi_en] += 1

    existing_embeddings = Instrument.objects.exclude(
        embedding_en__isnull=True
    ).only('tuotenimi', 'merkki_ja_malli', 'embedding_en')

    for instrument in existing_embeddings:
        cache_key = _get_cache_key(instrument)
        embedding_cache[cache_key] = instrument.embedding_en

    existing_enrichments = Instrument.objects.exclude(
        enriched_description__in=INVALID_ENRICHMENT_VALUES
    ).only('tuotenimi', 'merkki_ja_malli', 'enriched_description')

    for instrument in existing_enrichments:
        cache_key = _get_cache_key(instrument)
        enrichment_cache[cache_key] = instrument.enriched_description

    translation_cache = {
        key: counter.most_common(1)[0][0] for key, counter in key_translation_counts.items()
    }

    return translation_cache, enrichment_cache, embedding_cache

def _process_batch(batch, session, skip_enrichment, caches, on_error):
    """Processes batch by translating missing names, enriching missing descriptions, and generating embeddings."""
    translation_cache, enrichment_cache, embedding_cache = caches

    # Step 1: Analyze what each instrument needs (translation, enrichment, embedding, or all)
    instrument_states, unique_names_to_process = _collect_instrument_states(
        batch,
        caches,
    )

    # Step 2: Enrich any instruments not in cache via API
    if unique_names_to_process:
        enrich_instruments_batch(
            unique_names_to_process, 
            translation_cache, 
            enrichment_cache, 
            on_error
        )

    # Step 3: Update states from the newly populated caches
    _resolve_translations_and_enrichments(
        instrument_states,
        (translation_cache, enrichment_cache),
    )   

    # Step 4: Identify which instruments need embeddings
    instruments_needing_embedding = _identify_missing_embeddings(
        instrument_states,
        embedding_cache
    )

    # Step 5: Generate embeddings for instruments needing embeddings not in cache
    _embed_missing(
        instruments_needing_embedding,
        session,
        caches,
        on_error,
    )

    # Step 6: Prepare instruments with final translations, enrichments and embeddings
    return _build_instruments_to_update(
        instrument_states,
        embedding_cache
    )

def _collect_instrument_states(batch, caches):
    """
    Analyzes batch to determine what processing each instrument needs.
    
    Note: Existing valid translations are never overwritten, supporting multiple 
    valid translations for the same Finnish name.
    """
    translation_cache, enrichment_cache, embedding_cache = caches

    instrument_states = []
    unique_items_to_process = {}

    for instrument in batch:
        cache_key = _get_cache_key(instrument)

        # If DB has a value, mark as valid (User Override protection)
        has_valid_translation = instrument.tuotenimi_en not in INVALID_TRANSLATION_VALUES
        resolved_translation = instrument.tuotenimi_en if has_valid_translation else translation_cache.get(cache_key)

        has_valid_enrichment = instrument.enriched_description not in INVALID_ENRICHMENT_VALUES
        resolved_enrichment = instrument.enriched_description if has_valid_enrichment else enrichment_cache.get(cache_key)

        # If we are missing EITHER valid data OR a cached value, we need to process it
        needs_trans = not has_valid_translation and resolved_translation is None
        needs_enrich = not has_valid_enrichment and resolved_enrichment is None
        
        if (needs_trans or needs_enrich) and cache_key not in unique_items_to_process:
            brand_info = instrument.merkki_ja_malli or ""
            unique_items_to_process[cache_key] = {
                'finnish_name': instrument.tuotenimi, # MUST be 'finnish_name'
                'brand_model': brand_info
            }

        # Check embedding
        resolved_embedding = instrument.embedding_en
        if resolved_embedding is None:
            resolved_embedding = embedding_cache.get(cache_key)

        instrument_states.append(
            InstrumentState(
                instrument=instrument,
                cache_key=cache_key,
                has_valid_translation=has_valid_translation, 
                resolved_translation=resolved_translation,
                resolved_embedding=resolved_embedding,
                has_valid_enrichment=has_valid_enrichment,
                resolved_enrichment=resolved_enrichment,
            )
        )

    return instrument_states, unique_items_to_process

def _resolve_translations_and_enrichments(instrument_states, caches):
    """
    Updates instrument states with newly cached translations and enrichments.
    """
    translation_cache, enrichment_cache = caches
    for state in instrument_states:
        if state.resolved_translation is None:
            state.resolved_translation = translation_cache.get(state.cache_key,"Translation Failed")
        if state.resolved_enrichment is None:
            state.resolved_enrichment = enrichment_cache.get(state.cache_key, "Enrichment Failed")

def _identify_missing_embeddings(instrument_states, embedding_cache):
    """
    Identifies which instruments still need embeddings generated.
    """
    instruments_needing_embedding = set()
    for state in instrument_states:
        if state.resolved_embedding is None:
            cached_embedding = embedding_cache.get(state.cache_key)
            if cached_embedding is not None:
                state.resolved_embedding = cached_embedding
            else:
                instruments_needing_embedding.add(state.cache_key)

    return instruments_needing_embedding

def _embed_missing(instruments_needing_embedding, session, caches, on_error):
    """
    Generates embeddings for instruments via /embed_en_batch endpoint.
    Updates embedding cache. Marks failures as None.
    """
    translation_cache, enrichment_cache, embedding_cache = caches
    texts_to_embed = []
    names_to_embed = []
    for cache_key in instruments_needing_embedding:
        translation = translation_cache.get(cache_key) or ""
        enrichment = enrichment_cache.get(cache_key) or ""

        if translation in INVALID_TRANSLATION_VALUES:
            translation = ""
        if enrichment in INVALID_ENRICHMENT_VALUES:
            enrichment = ""

        combined_text = f"{translation} {enrichment}".strip()
        if combined_text:  # Only embed if we have some text
            texts_to_embed.append(combined_text)
            names_to_embed.append(cache_key)
    if texts_to_embed:
        try:
            response = session.post(
                f"{SERVICE_URL}/embed_en_batch",
                json={"texts": texts_to_embed},
                timeout=30
            )
            response.raise_for_status()

            embeddings_result = response.json().get('embeddings', [])

            for cache_key, embedding in zip(names_to_embed, embeddings_result, strict=True):
                embedding_cache[cache_key] = embedding

        except requests.exceptions.RequestException as exc:
            on_error(f'Error connecting to batch embedding service: {exc}')
            for cache_key in names_to_embed:
                embedding_cache[cache_key] = None

        except Exception as exc:
            on_error(f'Unexpected error during batch embedding: {exc}')
            for cache_key in names_to_embed:
                embedding_cache[cache_key] = None

def _build_instruments_to_update(instrument_states, embedding_cache):
    """
    Builds list of instruments to update with final translations, enrichments and embeddings.
    """
    instruments_to_update = []
    for state in instrument_states:
        instrument = state.instrument
        translation = state.resolved_translation

        if not state.has_valid_translation:
            instrument.tuotenimi_en = translation or "Translation Failed"

        if state.resolved_embedding is None:
            state.resolved_embedding = embedding_cache.get(state.cache_key)

        if instrument.embedding_en is None and state.resolved_embedding is not None:
            instrument.embedding_en = state.resolved_embedding

        if not state.has_valid_enrichment:
            instrument.enriched_description = state.resolved_enrichment or "Enrichment Failed"

        instruments_to_update.append(instrument)
    return instruments_to_update
