"""
Instrument Service

Handles the creation and updating of instruments in the database.
Includes translation, enrichment and embedding generation.
"""

from ..models import Instrument
from .enrichment import EnrichmentService
from ..embedding import INVALID_TRANSLATION_VALUES, INVALID_ENRICHMENT_VALUES
from simple_history.utils import bulk_update_with_history
from django.db import transaction
from collections import Counter
import requests

class InstrumentService:
    def __init__(self):
        self.enrichment_service = EnrichmentService()

    def create_instrument(self, instrument_data):
        tuotenimi = instrument_data.get('tuotenimi', '').lower()
        merkki_ja_malli = instrument_data.get('merkki_ja_malli', '').lower()

        # Check if another instrument with same name already exists
        existing = self._find_existing_translation(tuotenimi, merkki_ja_malli)

        if existing:
            # Reuse existing translation, embeddings and enrichment
            instrument_data['tuotenimi_en'] = existing.tuotenimi_en
            instrument_data['embedding_en'] = existing.embedding_en
            instrument_data['enriched_description'] = existing.enriched_description
            return Instrument.objects.create(**instrument_data)
        else:
            # New unique name, translate and generate embeddings
            instrument = Instrument(**instrument_data)
            self._translate_enrich_and_update_embeddings(instrument)
            instrument.save()
            return instrument

    def update_instrument(self, instance, instrument_data, update_duplicates=False):
        # Get the original values before any changes are made
        original_tuotenimi = instance.tuotenimi
        original_tuotenimi_en = instance.tuotenimi_en

        # Manually update the instance with all validated data
        for attr, value in instrument_data.items():
            setattr(instance, attr, value)

        # Determine what fields changed
        tuotenimi_changed = instance.tuotenimi != original_tuotenimi
        tuotenimi_en_changed = instance.tuotenimi_en != original_tuotenimi_en

        # Update translation, enrichment and embeddings depending on which fields changed
        if tuotenimi_changed and tuotenimi_en_changed:
            self._translate_enrich_and_update_embeddings(instance, translation_changed=True)
        elif tuotenimi_changed:
            # Finnish name changed - check for existing translation first
            existing = self._find_existing_translation(instance.tuotenimi, instance.merkki_ja_malli)
            if existing:
                instance.tuotenimi_en = existing.tuotenimi_en
                instance.enriched_description = existing.enriched_description
                instance.embedding_en = existing.embedding_en
            else:
                # New name - translate it
                self._translate_enrich_and_update_embeddings(instance)
        elif tuotenimi_en_changed:
            self._update_embedding_en(instance)

        instance.save()

        if update_duplicates and tuotenimi_en_changed and not tuotenimi_changed:
            self._update_duplicates(instance)

        return instance

    def _translate_enrich_and_update_embeddings(self, instrument, translation_changed=False):
        enrichment = self.enrichment_service.enrich_single(instrument.tuotenimi, instrument.merkki_ja_malli)
        translated_text = enrichment.get('translation')
        description = enrichment.get('description')

        is_valid_translation = translated_text not in INVALID_TRANSLATION_VALUES
        is_valid_enrichment = description not in INVALID_ENRICHMENT_VALUES

        if is_valid_translation and is_valid_enrichment:
            # If the user has changed the translation, use the existing translation
            if translation_changed:
                combined_text = ": ".join(filter(None, [instrument.tuotenimi_en, description]))
            else:
                combined_text = ": ".join(filter(None, [translated_text, description]))
            
            data = self._post_to_service("/embed_en", {"text": combined_text})
            embedding_en = data.get('embedding') if data else None
        else:
            embedding_en = None

        if not translation_changed:
            instrument.tuotenimi_en = translated_text
        instrument.enriched_description = description
        instrument.embedding_en = embedding_en

    def _update_duplicates(self, instance):
        # Find all other instruments with the same name and model
        duplicate_instruments = list(Instrument.objects.filter(
            tuotenimi__iexact=instance.tuotenimi,
            merkki_ja_malli__iexact=instance.merkki_ja_malli
        ).exclude(pk=instance.pk))

        # Update each duplicate
        for instrument in duplicate_instruments:
            instrument.tuotenimi_en = instance.tuotenimi_en
            instrument.enriched_description = instance.enriched_description
            instrument.embedding_en = instance.embedding_en
        
        with transaction.atomic():
            bulk_update_with_history(
                duplicate_instruments,
                Instrument,
                ['tuotenimi_en', 'enriched_description', 'embedding_en']
            )

    def _find_existing_translation(self, tuotenimi, merkki_ja_malli):
        # Normalize inputs to handle None as empty strings
        tn = (tuotenimi or "").strip()
        mm = (merkki_ja_malli or "").strip()

        existing = Instrument.objects.filter(
            tuotenimi__iexact=tn,
            merkki_ja_malli__iexact=mm
        ).exclude(
            tuotenimi_en__in=["", "Translation Failed"]
        ).values_list('tuotenimi_en', 'enriched_description', 'embedding_en')
        
        if not existing:
            return None
        
        # Majority voting
        translations = [t[0] for t in existing]
        most_common_translation = Counter(translations).most_common(1)[0][0]
        
        # Return the specific record
        return Instrument.objects.filter(
            tuotenimi__iexact=tn,
            merkki_ja_malli__iexact=mm,
            tuotenimi_en=most_common_translation
        ).first()

    def _update_embedding_en(self, instrument):
        combined_text = ": ".join(filter(None, [instrument.tuotenimi_en, instrument.enriched_description]))
        data = self._post_to_service("/embed_en", {"text": combined_text})
        embedding_en = data.get('embedding') if data else None

        instrument.embedding_en = embedding_en

    def _post_to_service(self, endpoint, payload):
        url = f"http://semantic-search-service:8001{endpoint}"
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=5.0
            )
            response.raise_for_status()
        except (requests.Timeout, requests.RequestException):
            return None

        try:
            return response.json()
        except ValueError:
            return None
