from django.apps import AppConfig

class InstrumentRegistryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'instrument_registry'

    def ready(self):
        from simple_history.signals import pre_create_historical_record
        from .models import HistoricalInstrument, HistoricalInstrumentAttachment
        from .signals import add_history_username
        # Import signals module to register the pre_delete signal
        from . import signals

        pre_create_historical_record.connect(
            add_history_username,
            sender=HistoricalInstrument
        )

        pre_create_historical_record.connect(
            add_history_username,
            sender=HistoricalInstrumentAttachment
        )

