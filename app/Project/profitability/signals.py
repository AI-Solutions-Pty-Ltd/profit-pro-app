from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from app.Project.models import (
    LabourCostTracker,
    MaterialCostTracker,
    OverheadCostTracker,
    PlantCostTracker,
    SubcontractorCostTracker,
)

from .utils import sync_tracker_to_journal


@receiver(post_save, sender=LabourCostTracker)
@receiver(post_save, sender=MaterialCostTracker)
@receiver(post_save, sender=PlantCostTracker)
@receiver(post_save, sender=OverheadCostTracker)
@receiver(post_save, sender=SubcontractorCostTracker)
def auto_sync_tracker_to_journal(sender, instance, created, **kwargs):
    """Automatically sync cost tracker to journal on save."""
    sync_tracker_to_journal(instance)


@receiver(post_delete, sender=LabourCostTracker)
@receiver(post_delete, sender=MaterialCostTracker)
@receiver(post_delete, sender=PlantCostTracker)
@receiver(post_delete, sender=OverheadCostTracker)
@receiver(post_delete, sender=SubcontractorCostTracker)
def auto_delete_tracker_from_journal(sender, instance, **kwargs):
    """Automatically remove cost tracker from journal on delete."""
    sync_tracker_to_journal(instance, deleted=True)
