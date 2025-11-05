from django.core.management.base import BaseCommand
from instrument_registry.embedding import precompute_instrument_embeddings

class Command(BaseCommand):
    help = 'Pre-computes and stores embeddings and translations for all instruments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of instruments to process in a single batch.'
        )
        # Might be useful for model update or data corruption
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-processing of all instruments, even if already processed.'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        force_reprocess = options['force']

        summary = precompute_instrument_embeddings(
            batch_size=batch_size,
            force=force_reprocess,
            on_info=lambda message: self.stdout.write(self.style.SUCCESS(message)),
            on_error=lambda message: self.stdout.write(self.style.ERROR(message)),
        )

        self.stdout.write(self.style.SUCCESS('\nFinished processing all instruments.'))
        self.stdout.write(self.style.SUCCESS(
            f'\n=== Summary ===\n'
            f'Total processed: {summary["processed_count"]}\n'
            f'Successful: {summary["successful"]}\n'
            f'Failed: {summary["failed"]}\n'
            f'Unique translations: {summary["cache_size"]}'
        ))
