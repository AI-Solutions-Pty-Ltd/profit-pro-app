from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce


class SoftDeleteManager(models.Manager):
    """Custom manager that excludes soft-deleted objects by default."""

    def get_queryset(self):
        """Return queryset excluding soft-deleted objects."""
        return super().get_queryset().filter(deleted=False)


class AllObjectsManager(models.Manager):
    """Manager that includes all objects, even soft-deleted ones."""

    pass


class BaseModel(models.Model):
    """Abstract model for time-stamped models with soft delete support.

    Attributes:
        created_at (DateTimeField): The date and time when the object was created.
        updated_at (DateTimeField): The date and time when the object was last updated.
        deleted (BooleanField): Soft delete flag.

    Managers:
        objects (SoftDeleteManager): Default manager that excludes soft-deleted objects.
        all_objects (AllObjectsManager): Manager that includes all objects, even soft-deleted ones.

    Usage:
        # Get only active (non-deleted) objects
        MyModel.objects.all()

        # Get all objects including soft-deleted ones
        MyModel.all_objects.all()

        # Soft delete an object
        obj.soft_delete()

        # Restore a soft-deleted object
        obj.restore()
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

    if TYPE_CHECKING:
        id: int

    # Default manager excludes soft-deleted objects
    objects = SoftDeleteManager()
    # Manager to access all objects including soft-deleted ones
    all_objects = AllObjectsManager()

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


def sum_queryset(queryset, field: str) -> Decimal:
    """Helper function to sum total price of queryset"""
    value = queryset.aggregate(
        sum=Coalesce(
            Sum(field),
            Value(0),
            output_field=DecimalField(),
        )
    )["sum"]
    if not value:
        return Decimal(0)
    return value
