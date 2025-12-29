from rest_framework import serializers
import requests
from .models import Instrument, RegistryUser, InstrumentAttachment
from .enrichment import EnrichmentService
from collections import Counter
from django.db import transaction
from simple_history.utils import bulk_update_with_history

# Mixin to clean whitespace from all CharFields
class WhitespaceCleaningSerializerMixin:
    def to_internal_value(self, data):
        from .util import clean_whitespace
        
        # Create a mutable copy of the data
        if hasattr(data, 'copy'):
            data = data.copy()
        else:
            data = dict(data)

        # Clean whitespace for all string fields provided in the data
        for key, value in data.items():
            if isinstance(value, str):
                # Check if this field exists on the serializer and is a CharField
                field = self.fields.get(key)
                if field and isinstance(field, serializers.CharField):
                    data[key] = clean_whitespace(value)

        return super().to_internal_value(data)

# Default instrument serializer for views and such.
class InstrumentSerializer(WhitespaceCleaningSerializerMixin, serializers.ModelSerializer):
    # If true, update English name for all instruments with the same Finnish name
    update_duplicates = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = Instrument
        exclude = ['embedding_en', 'enriched_description']

    def create(self, validated_data):
        tuotenimi = validated_data.get('tuotenimi', '').lower()
        merkki_ja_malli = validated_data.get('merkki_ja_malli', '').lower()

        # Check if another instrument with same name already exists
        existing = self._find_existing_translation(tuotenimi, merkki_ja_malli)

        if existing:
            # Reuse existing translation, embeddings and enrichment
            validated_data['tuotenimi_en'] = existing.tuotenimi_en
            validated_data['embedding_en'] = existing.embedding_en
            validated_data['enriched_description'] = existing.enriched_description
            return Instrument.objects.create(**validated_data)
        else:
            # New unique name, translate and generate embeddings
            instrument = Instrument(**validated_data)
            self._translate_enrich_and_update_embeddings(instrument)
            instrument.save()
            return instrument

    def update(self, instance, validated_data):
        # Pop the update_duplicates flag from the validated_data so it's not set on the instance
        update_duplicates_flag = validated_data.pop('update_duplicates', False)

        # Get the original values before any changes are made
        original_tuotenimi = instance.tuotenimi
        original_tuotenimi_en = instance.tuotenimi_en

        # Manually update the instance with all validated data
        for attr, value in validated_data.items():
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

        if update_duplicates_flag and tuotenimi_en_changed and not tuotenimi_changed:
            self._update_duplicates(instance)

        return instance

    def _update_duplicates(self, instance):
        # Find all other instruments with the same 'tuotenimi'
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

    def _translate_enrich_and_update_embeddings(self, instrument, translation_changed=False):
        enrichment = EnrichmentService().enrich_single(instrument.tuotenimi, instrument.merkki_ja_malli)
        translated_text = enrichment.get('translation')
        description = enrichment.get('description')
        
        # If the user has changed the translation, use the existing translation
        if translation_changed:
            combined_text = ": ".join(filter(None, [instrument.tuotenimi_en, description]))
        else:
            combined_text = ": ".join(filter(None, [translated_text, description]))
        
        data = self._post_to_service("/embed_en", {"text": combined_text})
        embedding_en = data.get('embedding')
        
        if (
            not translated_text
            or translated_text.strip() == "Translation Failed"
            or not description
            or description.strip() == "Enrichment Failed"
            or not embedding_en
        ):
            raise serializers.ValidationError(
                "Translation or embedding generation failed. Please try again."
            )

        if not translation_changed:
            instrument.tuotenimi_en = translated_text
        instrument.enriched_description = description
        instrument.embedding_en = embedding_en

    def _update_embedding_en(self, instrument):
        combined_text = ": ".join(filter(None, [instrument.tuotenimi_en, instrument.enriched_description]))
        data = self._post_to_service("/embed_en", {"text": combined_text})
        embedding_en = data.get('embedding')

        if not embedding_en:
            raise serializers.ValidationError(
                "Semantic search service could not generate English embeddings. Please try again."
            )

        instrument.embedding_en = embedding_en

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

    def _post_to_service(self, endpoint, payload):
        url = f"http://semantic-search-service:8001{endpoint}"
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=5.0
            )
            response.raise_for_status()
        except requests.Timeout:
            raise serializers.ValidationError("Semantic search service request timed out.")
        except requests.RequestException as exc:
            raise serializers.ValidationError(f"Semantic search service error: {exc}")

        try:
            return response.json()
        except ValueError:
            raise serializers.ValidationError("Semantic search service returned invalid JSON.")


# Instrument serializer for CSV import/export.
class InstrumentCSVSerializer(WhitespaceCleaningSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Instrument
        exclude = ['id', 'embedding_en', 'enriched_description']

# User serializer
class RegistryUserSerializer(WhitespaceCleaningSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = RegistryUser
        fields = ['id', 'email', 'full_name', 'password', 'is_staff', 'is_superuser', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.is_staff = validated_data.get('is_staff', instance.is_staff)
        instance.is_superuser = validated_data.get('is_superuser', instance.is_superuser)
        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def create(self, validated_data):
        user = RegistryUser.objects.create(**validated_data)
        user.set_password(user.password)
        user.save()
        return user

# Attachment serializer
class InstrumentAttachmentSerializer(WhitespaceCleaningSerializerMixin, serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = InstrumentAttachment
        fields = ['id', 'instrument', 'file', 'file_url', 'filename', 'file_type',
                  'file_size', 'description', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by', 'uploaded_by_name', 'file_url']

    def validate_file(self, value):
        """Validate file size"""
        from django.conf import settings
        if value.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            raise serializers.ValidationError('File size exceeds 20MB limit.')
        return value

    def get_file_url(self, obj):
        request = self.context.get('request')
        # Only return file URL if user is authenticated
        if request and request.user and request.user.is_authenticated:
            if obj.file and hasattr(obj.file, 'url'):
                if request is not None:
                    return request.build_absolute_uri(obj.file.url)
                return obj.file.url
        return None
