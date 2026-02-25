"""Procurement Tracker model for tracking purchases."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class ProcurementTracker(BaseModel):
    """Track procurement and purchases."""

    class DeliveryStatus(models.TextChoices):
        ORDERED = "ORDERED", "Ordered"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARTIAL = "PARTIAL", "Partial"
        PAID = "PAID", "Paid"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="procurement_trackers",
        help_text="Project this procurement belongs to",
    )
    item = models.CharField(max_length=255, help_text="Item description")
    supplier = models.CharField(max_length=255, help_text="Supplier name")
    ordered_date = models.DateField(help_text="Date ordered")
    invoice_number = models.CharField(
        max_length=100, blank=True, help_text="Invoice number"
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Quantity ordered"
    )
    delivery_status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.ORDERED,
        help_text="Delivery status",
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        help_text="Payment status",
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.item} - {self.supplier}"

    class Meta:
        verbose_name = "Procurement Tracker"
        verbose_name_plural = "Procurement Trackers"
        ordering = ["-ordered_date", "-created_at"]
