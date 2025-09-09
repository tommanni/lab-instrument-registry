from django.core.management.base import BaseCommand
from instrument_registry.util import csv_to_model
from instrument_registry.models import Instrument
from instrument_registry.serializers import InstrumentCSVSerializer
from datetime import date
import csv
import re
"""
A manage.py command that imports the contents of a csv file to the instrument table.
"""
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument("-m", "--mode", type=str, choices=["default", "old"], default="default")

    def handle(self, *args, **options):
        # default handling assumes that the csv has the same format as exported csv
        if options['mode'] == 'default':
            csv_path = options["csv_path"]
            with open(csv_path, "r", encoding="windows-1252") as file:
                csv_to_model(InstrumentCSVSerializer, file)
            return
        # the 'old' way of handling this, because the original csv provided by customer was janky
        elif options['mode'] == 'old':
            res = _read_csv(options["csv_path"])
            instruments = []
            for row in res:
                instruments.append(_to_Instrument(row))
            for i in instruments:
                i.save()

def _read_csv(csv_path):
    res = []
    with open(csv_path, "r", encoding="windows-1252") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            res.append(row)
    return res

# needed because our csv file has multiple date formats.
def _str_to_date(string):
    lst = re.split(r"[\s./-]", string)
    try:
        return date(int(lst[2]), int(lst[1]), int(lst[0]))
    except (ValueError, IndexError):
        return None

# changes colours from the csv to text in db
def _colour_to_text(string):
    if string == "w":
        return "Tarkistamatta"
    elif string == "y":
        return "Epäselvä/Keskeneräinen"
    elif string == "g":
        return "Saatavilla"
    else:
        return "Poistettu/Hukassa"

# assumes that the given column names are the same as the model field names.
def _to_Instrument(row: dict) -> Instrument:
	instance = Instrument()
	for f in Instrument._meta.get_fields():
		if f.name == "id": # skip id since it's automatically assigned
			continue
		if f.name == "toimituspvm" or f.name == "huoltosopimus_loppuu" or f.name == "seuraava_huolto" or f.name == "edellinen_huolto":
			setattr(instance, f.name, _str_to_date(row[f.name]))
		elif f.name == "tilanne":
			setattr(instance, f.name, _colour_to_text(row[f.name]))
		else:
			setattr(instance, f.name, row[f.name])
	return instance
