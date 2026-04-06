"""Materials Log model for tracking material deliveries."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class MaterialsLog(BaseModel):
    """Track materials received on site."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="materials_logs",
        help_text="Project this material log belongs to",
    )
    material_entity = models.ForeignKey(
        "Project.MaterialEntity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="materials_logs",
        help_text="Link to master material definition",
    )
    date_received = models.DateField(help_text="Date materials were received")
    supplier = models.CharField(
        max_length=255, blank=True, editable=False, help_text="Supplier name"
    )
    invoice_number = models.CharField(
        max_length=100, blank=True, help_text="Invoice number"
    )
    items_received = models.TextField(
        editable=False, help_text="Description of items received"
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Quantity received"
    )
    unit = models.CharField(
        max_length=50, blank=True, editable=False, help_text="Unit of measurement"
    )
    intended_usage = models.TextField(
        blank=True, help_text="Intended usage of materials"
    )
    comments = models.TextField(blank=True, help_text="Additional comments")

    def save(self, *args, **kwargs):
        """Synchronize fields from master entity if linked."""
        if self.material_entity:
            if not self.supplier:
                self.supplier = self.material_entity.supplier
            if not self.items_received:
                self.items_received = self.material_entity.name
            if not self.unit:
                self.unit = self.material_entity.unit
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.items_received} - {self.date_received}"

    class Meta:
        verbose_name = "Materials Log"
        verbose_name_plural = "Materials Logs"
        ordering = ["-date_received", "-created_at"]
