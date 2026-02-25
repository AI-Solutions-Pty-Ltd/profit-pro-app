"""Delivery Tracker model for tracking deliveries."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class DeliveryTracker(BaseModel):
    """Track deliveries to site."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="delivery_trackers",
        help_text="Project this delivery belongs to",
    )
    item = models.CharField(max_length=255, help_text="Item description")
    supplier = models.CharField(max_length=255, help_text="Supplier name")
    ordered_date = models.DateField(help_text="Date ordered")
    expected_delivery_date = models.DateField(
        blank=True, null=True, help_text="Expected delivery date"
    )
    actual_delivery_date = models.DateField(
        blank=True, null=True, help_text="Actual delivery date"
    )
    delivered_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Quantity delivered",
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.item} - {self.supplier}"

    class Meta:
        verbose_name = "Delivery Tracker"
        verbose_name_plural = "Delivery Trackers"
        ordering = ["-ordered_date", "-created_at"]
