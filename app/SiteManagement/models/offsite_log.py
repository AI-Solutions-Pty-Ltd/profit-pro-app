"""Off-Site Log model for tracking material/equipment removals."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class OffsiteLog(BaseModel):
    """Track materials and equipment removed from site."""

    class Condition(models.TextChoices):
        GOOD = "GOOD", "Good Condition"
        FAIR = "FAIR", "Fair Condition"
        POOR = "POOR", "Poor Condition"
        DAMAGED = "DAMAGED", "Damaged"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="offsite_logs",
        help_text="Project this off-site log belongs to",
    )
    date_removed = models.DateField(help_text="Date removed from site")
    item_description = models.TextField(help_text="Description of item")
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Quantity removed"
    )
    reason_for_removal = models.TextField(help_text="Reason for removal")
    removed_by = models.CharField(max_length=255, help_text="Person who removed item")
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD,
        help_text="Condition of equipment/material",
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.item_description[:50]} - {self.date_removed}"

    class Meta:
        verbose_name = "Off-Site Log"
        verbose_name_plural = "Off-Site Logs"
        ordering = ["-date_removed", "-created_at"]
