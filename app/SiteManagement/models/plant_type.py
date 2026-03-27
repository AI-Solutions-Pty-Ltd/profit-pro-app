"""Plant Type model for equipment tracking."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class PlantType(BaseModel):
    """Categorize plant and equipment and associated hourly rates."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="plant_types",
        help_text="Project this plant type belongs to",
    )
    name = models.CharField(max_length=100, help_text="Plant type name (e.g., Excavator, Crane, Generator)")
    hourly_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Hourly rate for this equipment type",
    )

    def __str__(self):
        return f"{self.name} ({self.hourly_rate}/hr)"

    class Meta:
        verbose_name = "Plant Type"
        verbose_name_plural = "Plant Types"
        ordering = ["name"]
        unique_together = ["project", "name"]
