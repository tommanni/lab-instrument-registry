from rest_framework import serializers
from .models import Instrument, RegistryUser, InstrumentAttachment
from .services.instruments import InstrumentService

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
        return InstrumentService().create_instrument(validated_data)

    def update(self, instance, validated_data):
        update_duplicates = validated_data.pop('update_duplicates', False)
        
        return InstrumentService().update_instrument(
            instance, 
            validated_data, 
            update_duplicates=update_duplicates
        )

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
