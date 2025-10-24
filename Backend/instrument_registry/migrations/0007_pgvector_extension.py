from django.db import migrations
from pgvector.django import VectorExtension

class Migration(migrations.Migration):
    dependencies = [
        ('instrument_registry', '0006_historicalinstrument_history_username'),
    ]

    operations = [
        VectorExtension(),
    ]