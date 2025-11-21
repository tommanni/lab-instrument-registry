from lingua import Language, LanguageDetectorBuilder
from instrument_registry.models import Instrument
from datetime import datetime
import io
import csv

# Returns a StringIO object containing model data in csv format based on the queryset.
def model_to_csv(serializer_class, queryset):
    serializer = serializer_class(instance=queryset, many=True)
    fieldnames = serializer_class().get_fields().keys()
    buffer = io.StringIO()
    writer = csv.DictWriter(f=buffer, delimiter=';', fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(serializer.data)
    buffer.seek(0)
    return buffer

# Creates and saves model instances based on the given file-like object.
def csv_to_model(serializer_class, csv_file):
    csv_file.seek(0)
    reader = csv.DictReader(f=csv_file, delimiter=';')
    data = []
    # remove empty string entries because serializer validation fails otherwise
    for row in reader:
        data.append({k:v for k,v in row.items() if v != ''})
    serializer = serializer_class(data=data, many=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()


def parse_date(date_str):
    """
    Parse a date string from a CSV file and return it in YYYY-MM-DD format.
    Handles common date formats like DD.MM.YYYY, MM/DD/YYYY, etc.
    Returns None if the date string is empty or cannot be parsed.
    """
    if not date_str:
        return None
    for fmt in ('%d.%m.%Y', '%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None

# Language detector setup for search terms    
LANGUAGE_DETECTOR = LanguageDetectorBuilder.from_languages(
    Language.ENGLISH,
    Language.FINNISH
).build()

ENGLISH_CONFIDENCE_MIN = 0.60
CONFIDENCE_MARGIN = 0.10
    
def should_translate_to_english(text: str) -> bool:
    """
    Decide whether to route the query through the Finnish->English translation step.
    We translate unless the detector is clearly confident the text is already English.
    """
    if not text:
        return True

    confidence_map = {
        confidence.language: confidence.value
        for confidence in LANGUAGE_DETECTOR.compute_language_confidence_values(text)
    }

    english_conf = confidence_map.get(Language.ENGLISH, 0.0)
    finnish_conf = confidence_map.get(Language.FINNISH, 0.0)

    is_confident_english = (
        english_conf >= ENGLISH_CONFIDENCE_MIN and
        english_conf - finnish_conf >= CONFIDENCE_MARGIN
    )

    return not is_confident_english


# Helper function to check for duplicate instruments
def check_csv_duplicates(rows):
    """
    Check which CSV rows are duplicates and which are new.

    A duplicate is defined as having the same combination of:
    - tay_numero
    - tuotenimi
    - merkki_ja_malli

    Args:
        rows: List of dictionaries from CSV DictReader

    Returns:
        tuple: (new_rows, duplicates, invalid_rows, new_count, duplicate_count, invalid_count)
    """
    new_rows = []
    duplicates = []
    invalid_rows = []

    # Fetch all existing instrument identifiers in a single query
    existing_instruments = set(
        Instrument.objects.values_list(
            'tay_numero',
            'tuotenimi',
            'merkki_ja_malli'
        )
    )

    for row in rows:
        tay_numero = row.get('tay_numero', '').strip()
        tuotenimi = row.get('tuotenimi', '').strip()
        merkki_ja_malli = row.get('merkki_ja_malli', '').strip()

        # Skip rows that don't have tuotenimi AND merkki_ja_malli
        if not tuotenimi and not merkki_ja_malli:
            invalid_rows.append({
                'tay_numero': tay_numero or '-',
                'tuotenimi': tuotenimi or '-',
                'merkki_ja_malli': merkki_ja_malli or '-'
            })
            continue

        # Check if this exact combination already exists in memory
        is_duplicate = (tay_numero, tuotenimi, merkki_ja_malli) in existing_instruments

        if is_duplicate:
            duplicates.append(row)
        else:
            new_rows.append(row)
            # Add the new combination to the set to handle duplicates within the CSV
            existing_instruments.add((tay_numero, tuotenimi, merkki_ja_malli))

    return new_rows, duplicates, invalid_rows, len(new_rows), len(duplicates), len(invalid_rows)
