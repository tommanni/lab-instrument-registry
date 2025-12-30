from ..models import Instrument
from enrichment import EnrichmentService

class InstrumentService:
    def __init__(self):
        self.enrichment_service = EnrichmentService()

    def create_instrument(self, instrument_data):
        instrument = Instrument.objects.create(**instrument_data)
        return instrument

    def update_instrument(self, instance, instrument_data, update_duplicates=False):
        instrument = Instrument.objects.get(id=instrument_data['id'])
        instrument.update(**instrument_data)
        return instrument
