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

from django.db import transaction, connection, close_old_connections
from django.db.models import Q
from django.conf import settings
from simple_history.utils import bulk_update_with_history

from instrument_registry.models import Instrument
from instrument_registry.services.enrichment import (
    enrich_instruments_batch, 
    INVALID_ENRICHMENT_VALUES
)

import requests
import threading
import concurrent.futures
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

def _requests_retry_session(pool_size=10):
    """
    Creates a session with a connection pool
    """
    session = requests.Session()
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504),
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=5, pool_maxsize=pool_size)
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
    batch_size: int = 50,
    max_workers: int = 6,
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
        instruments_queryset = Instrument.objects.filter(
            Q(tuotenimi_en__in=INVALID_TRANSLATION_VALUES) |
            Q(enriched_description__in=INVALID_ENRICHMENT_VALUES) |
            Q(embedding_en__isnull=True)
        )
        on_info('Processing instruments that need updates.')

    instruments = list(instruments_queryset)
    total_count = len(instruments)
    
    if total_count == 0:
        on_info("No instruments to process.")
        return {'processed_count': 0}

    # Create a Lock for the shared cache
    cache_lock = threading.Lock()

    translation_cache, enrichment_cache, embedding_cache = _build_caches()

    on_info(f'Starting to process {total_count} instruments in batches of {batch_size}.')

    batches = [instruments[i:i + batch_size] for i in range(0, total_count, batch_size)]

    # Execute batches in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map futures to their batch index for logging
        future_to_idx = {
            executor.submit(
                _process_batch_worker, 
                batch, 
                skip_enrichment,
                (translation_cache, enrichment_cache, embedding_cache), 
                cache_lock,
                max_workers,
                on_error
            ): i for i, batch in enumerate(batches)
        }

        # As tasks complete (in any order), write to DB
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                # Get the result from the worker
                instruments_to_update = future.result()

                # MAIN THREAD: Write to Database
                if instruments_to_update:
                    with transaction.atomic():
                        bulk_update_with_history(
                            instruments_to_update,
                            Instrument,
                            ['tuotenimi_en', 'enriched_description', 'embedding_en']
                        )
                    on_info(f'Batch {idx + 1}/{len(batches)} saved.')

            except Exception as exc:
                on_error(f'Batch {idx + 1} failed with error: {exc}')

    return {
        'processed_count': total_count,
        'successful': Instrument.objects.exclude(tuotenimi_en__in=["", "Translation Failed"]).count(),
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

def _process_batch_worker(batch, skip_enrichment, global_caches, cache_lock, pool_size, on_error):
    """
    Worker function: Handles Network I/O.
    """
    close_old_connections()

    # Create a session local to this thread
    session = _requests_retry_session(pool_size=pool_size)

    # Unpack shared global cahces
    global_trans_cache, global_enrich_cache, global_embed_cache = global_caches

    try:
        # Step 1: Analyze
        instrument_states, unique_items_to_process = _collect_instrument_states(batch, global_caches)

        # Step 2: Gemini API 
        if unique_items_to_process:
            #Create empty local dictionaries for this thread
            local_trans_sandbox = {}
            local_enrich_sandbox = {}

            enrich_instruments_batch(
                unique_items_to_process, 
                local_trans_sandbox, 
                local_enrich_sandbox, 
                on_error
            )

            # Merge local sandboxes into global caches
            with cache_lock:
                global_trans_cache.update(local_trans_sandbox)
                global_enrich_cache.update(local_enrich_sandbox)

            # Update local state from cache
            _resolve_translations_and_enrichments(instrument_states, (global_trans_cache, global_enrich_cache))

        # Step 3: Embeddings
        instruments_needing_embedding = _identify_missing_embeddings(
            instrument_states, 
            global_embed_cache
        )

        if instruments_needing_embedding:
            local_embed_sandbox = {}

            _embed_missing(
                instruments_needing_embedding, 
                session, 
                (global_trans_cache, global_enrich_cache), 
                local_embed_sandbox, 
                on_error
            )

            # Merge local sandbox into global cache
            with cache_lock:
                global_embed_cache.update(local_embed_sandbox)

        # Step 4: Return data to main thread
        return _build_instruments_to_update(instrument_states, global_embed_cache)

    finally:
        session.close()
        close_old_connections()

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

def _embed_missing(instruments_needing_embedding, session, source_caches, target_cache, on_error):
    """
    Generates embeddings for instruments via /embed_en_batch endpoint.
    Updates embedding cache (Sandbox). Marks failures as None.
    """
    translation_cache, enrichment_cache = source_caches

    texts_to_embed = []
    names_to_embed = []

    for cache_key in instruments_needing_embedding:
        translation = translation_cache.get(cache_key) or ""
        enrichment = enrichment_cache.get(cache_key) or ""

        is_valid_trans = translation and translation not in INVALID_TRANSLATION_VALUES
        is_valid_enrich = enrichment and enrichment not in INVALID_ENRICHMENT_VALUES

        if is_valid_trans and is_valid_enrich:
            combined_text = f"{translation}: {enrichment}"
            texts_to_embed.append(combined_text)
            names_to_embed.append(cache_key)
        else:
            target_cache[cache_key] = None

    if texts_to_embed:
        try:
            response = session.post(
                f"{SERVICE_URL}/embed_en_batch",
                json={"texts": texts_to_embed},
                timeout=60
            )
            response.raise_for_status()
            embeddings_result = response.json().get('embeddings', [])

            for cache_key, embedding in zip(names_to_embed, embeddings_result, strict=True):
                target_cache[cache_key] = embedding

        except requests.exceptions.RequestException as exc:
            on_error(f'Error connecting to batch embedding service: {exc}')
            for cache_key in names_to_embed:
                target_cache[cache_key] = None

        except Exception as exc:
            on_error(f'Unexpected error during batch embedding: {exc}')
            for cache_key in names_to_embed:
                target_cache[cache_key] = None

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
