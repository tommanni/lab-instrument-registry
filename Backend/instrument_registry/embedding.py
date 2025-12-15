"""
Instrument Translation and Embedding Pipeline

This module handles the automated translation of instrument names from Finnish to English
and generates semantic embeddings for search functionality. The system is designed to handle 
multiple instruments with the same Finnish name (tuotenimi) but with
different valid English translations (tuotenimi_en).

DESIGN CHOICES:
- Instruments with existing valid translations are never automatically overwritten
- When multiple translations exist for the same Finnish name, majority voting determines
  the "canonical" translation for new instruments
- Translations and embeddings are cached to minimize API calls to the semantic service
- Batch processing is used for efficiency

WORKFLOW:
1. Build caches from existing database records:
   - name_translation_cache: Finnish name → most common English translation
   - embedding_by_translation: English translation → embedding vector
2. For each batch of instruments:
   a. Collect state (which need translation, which need embedding)
   b. Translate missing Finnish names via semantic service
   c. Identify which English translations still need embeddings
   d. Generate embeddings for missing translations
   e. Update instruments in database atomically

ERROR HANDLING:
- Translation failures are marked with "Translation Failed" string
- Embedding failures are marked with None
- Both are tracked in INVALID_TRANSLATION_VALUES to prevent re-processing
"""

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


# Translation values that indicate a missing or failed translation
INVALID_TRANSLATION_VALUES = {"", "Translation Failed"}

SERVICE_URL = getattr(settings, 'SEMANTIC_SERVICE_URL', 'http://semantic-search-service:8001')

def precompute_instrument_embeddings(
    *,
    batch_size: int = 100,
    force: bool = False,
    on_info=lambda msg: None,
    on_error=lambda msg: None,
):
    """
    Main entry point for precomputing translations and embeddings for instruments.
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

            instruments_to_update = _process_batch(
                batch, 
                session, 
                (name_translation_cache, embedding_by_translation), 
                on_error
            )

            # Save batch to database atomically with django-simple-history utility function to track history
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
    
    This function implements a majority voting system for translations. Since multiple
    instruments can have the same Finnish name but different English translations
    (by design), we count all occurrences and use the most common translation as the
    default for instruments that don't yet have a translation.
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
        # Count occurrences of each translation for this Finnish name (for majority voting)
        name_translation_counts[tuotenimi_key][translation_value] += 1
        # Cache embedding for each unique translation
        if instrument.embedding_en is not None and translation_value not in embedding_by_translation:
            embedding_by_translation[translation_value] = instrument.embedding_en

    # Use majority voting: for each Finnish name, pick the most common English translation
    name_translation_cache = {
        key: counter.most_common(1)[0][0] for key, counter in name_translation_counts.items()
    }

    return embedding_by_translation, name_translation_cache

def _process_batch(batch, session, caches, on_error):
    """
    Processes a batch of instruments by translating missing Finnish names and generating embeddings.
    """
    name_translation_cache, embedding_by_translation = caches

    # Step 1: Analyze what each instrument needs (translation, embedding, or both)
    batch_states, unique_names_to_translate = _collect_batch_state(
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

    # Step 3: Update batch_states with new translations and identify which need embeddings
    translations_needing_embedding = _resolve_translations_and_identify_missing_embeddings(
        batch_states,
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
        batch_states,
        embedding_by_translation
    )

    return instruments_to_update

def _collect_batch_state(batch, name_translation_cache, embedding_by_translation):
    """
    Analyzes a batch of instruments to determine what processing is needed.
    
    For each instrument, this function determines:
    1. Does it have a valid existing translation? (If yes, keep it)
    2. If not, can we use a cached translation from similar instruments?
    3. If not cached, mark the Finnish name for translation via API
    4. Does it need an embedding? (Check instrument first, then cache)
    
    Note:
        Existing valid translations on instruments are NEVER overwritten (has_valid_translation=True),
        respecting the system's design that allows multiple translations for the same Finnish name.
    """
    batch_states = []
    unique_names_to_translate = {}

    for instrument in batch:
        name = instrument.tuotenimi or ""
        tuotenimi_key = name.lower()

        # Check if this instrument already has a valid translation
        # If yes, we NEVER overwrite it
        has_valid_translation = instrument.tuotenimi_en not in INVALID_TRANSLATION_VALUES
        # Use existing translation if valid, otherwise try to get from cache (majority vote)
        desired_translation = instrument.tuotenimi_en if has_valid_translation else name_translation_cache.get(tuotenimi_key)

        # If no valid translation exists and not in cache, mark for API translation
        if (
            not has_valid_translation
            and desired_translation is None
            and tuotenimi_key not in unique_names_to_translate
        ):
            # Store original-case Finnish name for API call
            unique_names_to_translate[tuotenimi_key] = instrument.tuotenimi

        # Try to get embedding from instrument first, then from cache
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

def _translate_missing(unique_names_to_translate, session, caches, on_error):
    """
    Translates Finnish instrument names to English via the semantic search service.
    
    Makes a batch API call to /process_batch endpoint which returns both translations
    and embeddings. Updates both caches with the results.
    
    Note:
        On any error (network, timeout, API error), all names in the batch are marked
        as "Translation Failed" to prevent infinite retry loops.
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
    Updates batch state with newly cached translations and identifies which need embeddings.
    
    This function runs after _translate_missing has potentially added new translations to the cache.
    It performs a second pass over batch_states to:
    1. Fill in any desired_translation values that were None (from newly cached translations)
    2. Check if embeddings are now available in the cache
    3. Build a set of English translations that still need embeddings generated
    
    Note:
        This two-pass approach (collect → translate → resolve) allows us to batch
        translation API calls efficiently while still handling all edge cases.
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
    Generates embeddings for English translations via the semantic search service.
    
    This function is called when we have English translations (either from existing
    instruments or from _translate_missing) but don't have embeddings for them yet.
    
    Note:
        On any error, all texts in the batch get None embeddings (graceful degradation).
        Instruments will be saved with translations but without embeddings for search.
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

def _build_instruments_to_update(batch_states, embedding_by_translation):
    """
    Prepares instruments for database update by applying translations and embeddings.
    
    This function finalizes the state of each instrument by:
    1. Setting tuotenimi_en if the instrument didn't have a valid translation
       (uses desired_translation from state, or "Translation Failed" as fallback)
    2. Setting embedding_en if available in the cache and not already on instrument
    """
    instruments_to_update = []
    for state in batch_states:
        instrument = state['instrument']
        translation = state['desired_translation']

        # Apply translation to instruments that didn't have one
        if not state['has_valid_translation']:
            instrument.tuotenimi_en = translation or "Translation Failed"

        # Check cache again for embeddings: they may have been added by _translate_missing
        # or _embed_missing after the initial state collection
        if (
            state['resolved_embedding'] is None and
            translation not in INVALID_TRANSLATION_VALUES
        ):
            state['resolved_embedding'] = embedding_by_translation.get(translation)

        # Apply embedding to instruments that don't have one
        if instrument.embedding_en is None and state['resolved_embedding'] is not None:
            instrument.embedding_en = state['resolved_embedding']

        instruments_to_update.append(instrument)
    return instruments_to_update
