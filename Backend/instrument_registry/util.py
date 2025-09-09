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