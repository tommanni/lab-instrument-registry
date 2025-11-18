from django.db.models.signals import pre_delete
from django.dispatch import receiver


def add_history_username(sender, **kwargs):
    history_instance = kwargs['history_instance']
    if history_instance.history_user:
        history_instance.history_username = history_instance.history_user.full_name


@receiver(pre_delete, sender='instrument_registry.InstrumentAttachment')
def delete_attachment_file(sender, instance, **kwargs):
    """
    Delete the file from filesystem when an InstrumentAttachment is deleted.
    This ensures files are cleaned up when an instrument is deleted (CASCADE).
    """
    if instance.file:
        try:
            instance.file.delete(save=False)
        except Exception as e:
            # Log the error but don't prevent deletion
            print(f"Error deleting file {instance.filename}: {e}")
