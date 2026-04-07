from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.projects.projects_models import Project


def material_invoice_upload_path(instance, filename):
    """
    STUB: Kept for migration compatibility (see migration 0074).
    The field was moved to MaterialEntity in migration 0075.
    """
    return f"profitability/materials/invoices/{instance.project.pk}/{filename}"


class MaterialCostTracker(BaseModel):
    """
    Material cost tracking log for monitoring project expenditures.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="material_cost_logs",
        help_text="Project this cost log belongs to",
    )
    material_entity = models.ForeignKey(
        "Project.MaterialEntity",
        on_delete=models.CASCADE,
        related_name="cost_logs",
        help_text="Link to master material definition",
    )
    date = models.DateField(help_text="Date of monitoring")
    invoice_number = models.CharField(
        max_length=100, blank=True, help_text="Invoice number for the transaction"
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Quantity of material used/bought",
    )
    rate = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Rate per unit"
    )

    @property
    def cost(self):
        """Calculate total cost."""
        return self.quantity * self.rate

    def save(self, *args, **kwargs):
        """Auto-populate fields from linked entity if missing."""
        if self.material_entity:
            if not self.invoice_number:
                self.invoice_number = self.material_entity.invoice_number
            if self.rate == 0:
                self.rate = self.material_entity.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.material_entity.name} - {self.date} - {self.cost}"

    class Meta:
        verbose_name = "Material Cost Tracker"
        verbose_name_plural = "Material Cost Trackers"
        ordering = ["-date", "-created_at"]
