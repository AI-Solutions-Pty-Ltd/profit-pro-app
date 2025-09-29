from django.db import models


class BaseModel(models.Model):
    """Abstract model for time-stamped models with history tracking.

    Attributes:
        created_at (DateTimeField): The date and time when the object was created.
        updated_at (DateTimeField): The date and time when the object was last updated.
        history (HistoricalRecords): The history of changes to the object.
        deleted (BooleanField): Soft delete flag.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last modified",
    )
    deleted = models.BooleanField(default=False, help_text="Soft delete flag")

    class Meta:
        abstract = True

    def soft_delete(self):
        """Soft delete the instance by setting deleted=True"""
        self.deleted = True
        self.save(update_fields=["deleted"])

    def restore(self):
        """Restore a soft-deleted instance"""
        self.deleted = False
        self.save(update_fields=["deleted"])

    @property
    def is_deleted(self):
        """Check if the instance is soft-deleted"""
        return self.deleted
