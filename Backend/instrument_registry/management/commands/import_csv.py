from django.core.management.base import BaseCommand
from instrument_registry.util import csv_to_model, clean_whitespace
from instrument_registry.models import Instrument
from instrument_registry.serializers import InstrumentCSVSerializer
from pgvector.django import VectorField
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
    # Try different encodings to handle Excel exports
    encodings = ['utf-8-sig', 'utf-8', 'windows-1252', 'iso-8859-1']

    for encoding in encodings:
        try:
            with open(csv_path, "r", encoding=encoding) as file:
                # Try both comma and semicolon delimiters
                content = file.read()
                file.seek(0)

                # Detect delimiter by counting occurrences in first line
                first_line = file.readline()
                comma_count = first_line.count(',')
                semicolon_count = first_line.count(';')
                delimiter = ',' if comma_count > semicolon_count else ';'

                file.seek(0)
                reader = csv.DictReader(file, delimiter=delimiter)
                for row in reader:
                    res.append(row)
                print(f"Successfully read CSV with encoding: {encoding}, delimiter: '{delimiter}'")
                return res
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise ValueError(f"Could not read CSV file with any of the tried encodings: {encodings}")

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

# Column mapping from Excel CSV to Django model fields
EXCEL_TO_DJANGO_MAPPING = {
    'TAY-numero': 'tay_numero',
    'Tuotenimi': 'tuotenimi',
    'Merkki ja Malli': 'merkki_ja_malli',
    'Sarjanumero': 'sarjanumero',
    'Yksikkö': 'yksikko',
    'Kampus': 'kampus',
    'Rakennus': 'rakennus',
    'Huone': 'huone',
    'Vastuuhenkilö/Huonevastaava': 'vastuuhenkilo',
    'Toimituspvm': 'toimituspvm',
    'Toimittaja': 'toimittaja',
    'Lisätieto': 'lisatieto',
    'Vanha Sijainti': 'vanha_sijainti',
    'Tarkistettu': 'tarkistettu',
    'Esinetila': 'tilanne'
}

# Maps Excel column names to Django field names and handles the conversion
def _to_Instrument(row: dict) -> Instrument:
	instance = Instrument()
	for f in Instrument._meta.get_fields():
		if f.name == "id": # skip id since it's automatically assigned
			continue
		if isinstance(f, VectorField):
			# Skip vector fields; they are filled after embeddings are computed
			continue

		# Find the Excel column name that maps to this Django field
		excel_col = None
		for excel_name, django_name in EXCEL_TO_DJANGO_MAPPING.items():
			if django_name == f.name:
				excel_col = excel_name
				break

		# Get the value from the row using Excel column name
		if excel_col and excel_col in row:
			value = clean_whitespace(row[excel_col])
		else:
			value = ""  # Default empty value for missing columns

		# Handle special field types
		if f.name == "toimituspvm" or f.name == "huoltosopimus_loppuu" or f.name == "seuraava_huolto" or f.name == "edellinen_huolto":
			setattr(instance, f.name, _str_to_date(value) if value else None)
		elif f.name == "tilanne":
			setattr(instance, f.name, _colour_to_text(value) if value else "Tarkistamatta")
		else:
			setattr(instance, f.name, value if value else "")
	return instance
