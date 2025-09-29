from rest_framework import serializers
from .models import Instrument, RegistryUser

# Default instrument serializer for views and such.
class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = '__all__'

class HistoricalInstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument.history.model
        fields = '__all__'

# Instrument serializer for CSV import/export.
class InstrumentCSVSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        exclude = ['id']

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