from rest_framework import serializers
from .models import Instrument, RegistryUser
import requests

# Default instrument serializer for views and such.
class InstrumentSerializer(serializers.ModelSerializer):
    # If true, update English name for all instruments with the same Finnish name
    update_duplicates = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = Instrument
        exclude = ['embedding_fi', 'embedding_en']

    def create(self, validated_data):
        tuotenimi = validated_data.get('tuotenimi', '').lower()
        
        # Check if another instrument with same name already exists
        existing = self._find_existing_translation(tuotenimi)
        
        if existing:
            # Reuse existing translation and embeddings
            validated_data['tuotenimi_en'] = existing.tuotenimi_en
            validated_data['embedding_fi'] = existing.embedding_fi
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
            self._update_embedding_fi(instance)
            self._update_embedding_en(instance)
        elif tuotenimi_changed:
            # Finnish name changed - check for existing translation first
            existing = self._find_existing_translation(instance.tuotenimi)
            if existing:
                instance.tuotenimi_en = existing.tuotenimi_en
                instance.embedding_fi = existing.embedding_fi
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
        embedding_fi = data.get('embedding_fi')
        embedding_en = data.get('embedding_en')

        if (
            not translated_text
            or translated_text.strip().lower() == "translation failed"
            or not embedding_fi
            or not embedding_en
        ):
            raise serializers.ValidationError(
                "Semantic search service could not generate embeddings. Please try again."
            )

        instrument.tuotenimi_en = translated_text
        instrument.embedding_fi = embedding_fi
        instrument.embedding_en = embedding_en

    def _update_embedding_fi(self, instrument):
        data = self._post_to_service("/embed_fi", {"text": instrument.tuotenimi})
        embedding_fi = data.get('embedding')

        if not embedding_fi:
            raise serializers.ValidationError(
                "Semantic search service could not generate Finnish embeddings. Please try again."
            )

        instrument.embedding_fi = embedding_fi

    def _update_embedding_en(self, instrument):
        data = self._post_to_service("/embed_en", {"text": instrument.tuotenimi_en})
        embedding_en = data.get('embedding')

        if not embedding_en:
            raise serializers.ValidationError(
                "Semantic search service could not generate English embeddings. Please try again."
            )

        instrument.embedding_en = embedding_en

    def _find_existing_translation(self, tuotenimi):
        return Instrument.objects.filter(
            tuotenimi__iexact=tuotenimi
        ).exclude(
            tuotenimi_en__in=["", "Translation Failed"]
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
class InstrumentCSVSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        exclude = ['id', 'embedding_fi', 'embedding_en']

# User serializer
class RegistryUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistryUser
        fields = '__all__'
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
