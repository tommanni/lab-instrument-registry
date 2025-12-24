from rest_framework import serializers
import requests
from .models import Instrument, RegistryUser, InstrumentAttachment
from collections import Counter

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

        # Check if another instrument with same name already exists
        existing = self._find_existing_translation(tuotenimi)

        if existing:
            # Reuse existing translation and embeddings
            validated_data['tuotenimi_en'] = existing.tuotenimi_en
            validated_data['embedding_en'] = existing.embedding_en
            return Instrument.objects.create(**validated_data)
        else:
            # New unique name, translate and generate embeddings
            instrument = Instrument(**validated_data)
            self._translate_and_update_embeddings(instrument)
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

        # Update embeddings and translations depending on which fields changed
        if tuotenimi_changed and tuotenimi_en_changed:
            self._update_embedding_en(instance)
        elif tuotenimi_changed:
            # Finnish name changed - check for existing translation first
            existing = self._find_existing_translation(instance.tuotenimi)
            if existing:
                instance.tuotenimi_en = existing.tuotenimi_en
                instance.embedding_en = existing.embedding_en
            else:
                # New name - translate it
                self._translate_and_update_embeddings(instance)
        elif tuotenimi_en_changed:
            self._update_embedding_en(instance)

        instance.save()

        if update_duplicates_flag and tuotenimi_en_changed and not tuotenimi_changed:
            # Find all other instruments with the same 'tuotenimi'
            duplicate_instruments = Instrument.objects.filter(
                tuotenimi__iexact=instance.tuotenimi
            ).exclude(pk=instance.pk)

            # Update each duplicate
            cached_embedding = instance.embedding_en
            for instrument in duplicate_instruments:
                instrument.tuotenimi_en = instance.tuotenimi_en
                instrument.embedding_en = cached_embedding
                instrument.save(update_fields=["tuotenimi_en", "embedding_en"])


        return instance

    def _translate_and_update_embeddings(self, instrument):
        data = self._post_to_service("/process", {"text": instrument.tuotenimi})
        translated_text = data.get('translated_text')
        embedding_en = data.get('embedding_en')

        if (
            not translated_text
            or translated_text.strip().lower() == "translation failed"
            or not embedding_en
        ):
            raise serializers.ValidationError(
                "Semantic search service could not generate embeddings. Please try again."
            )

        instrument.tuotenimi_en = translated_text
        instrument.embedding_en = embedding_en

    def _update_embedding_en(self, instrument):
        data = self._post_to_service("/embed_en", {"text": instrument.tuotenimi_en})
        embedding_en = data.get('embedding')

        if not embedding_en:
            raise serializers.ValidationError(
                "Semantic search service could not generate English embeddings. Please try again."
            )

        instrument.embedding_en = embedding_en

    def _find_existing_translation(self, tuotenimi):
        # Get all valid translations for this Finnish name
        existing = Instrument.objects.filter(
            tuotenimi__iexact=tuotenimi
        ).exclude(
            tuotenimi_en__in=["", "Translation Failed"]
        ).values_list('tuotenimi_en', 'embedding_en')
        
        if not existing:
            return None
        
        # Use majority voting - pick most common translation
        translations = [t[0] for t in existing]
        most_common_translation = Counter(translations).most_common(1)[0][0]
        
        # Return first instrument with that translation
        return Instrument.objects.filter(
            tuotenimi__iexact=tuotenimi,
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
