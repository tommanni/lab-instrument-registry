from django.core.management.base import BaseCommand
from datetime import datetime
from instrument_registry.models import Instrument
from instrument_registry.serializers import InstrumentCSVSerializer
from instrument_registry.util import model_to_csv
from shutil import copyfileobj
"""
A manage.py command that exports the contents of the instrument table to a csv file.
"""
class Command(BaseCommand):

    def handle(self, *args, **options):
        path = ""
        now = datetime.now().strftime("%G-%m-%d")
        filename = "laiterekisteri_" + now + ".csv"

        with open(path + filename, "w", encoding="utf-8") as destination:
            source = model_to_csv(InstrumentCSVSerializer, Instrument.objects.all())
            copyfileobj(source, destination)