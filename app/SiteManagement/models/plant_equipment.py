"""Plant and Equipment model for tracking equipment usage."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class PlantEquipment(BaseModel):
    """Track plant and equipment usage and maintenance."""

    class BreakdownStatus(models.TextChoices):
        OPERATIONAL = "OPERATIONAL", "Operational"
        BREAKDOWN = "BREAKDOWN", "Breakdown"
        UNDER_MAINTENANCE = "UNDER_MAINTENANCE", "Under Maintenance"
        RETIRED = "RETIRED", "Retired"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="plant_equipment",
        help_text="Project this equipment belongs to",
    )
    date = models.DateField(help_text="Date of record")
    equipment_name = models.CharField(max_length=255, help_text="Plant/Equipment name")
    supplier = models.CharField(max_length=255, blank=True, help_text="Supplier/Owner")
    usage_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Usage hours",
    )
    breakdown_status = models.CharField(
        max_length=20,
        choices=BreakdownStatus.choices,
        default=BreakdownStatus.OPERATIONAL,
        help_text="Breakdown status",
    )
    maintenance_done = models.TextField(
        blank=True, help_text="Maintenance work performed"
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.equipment_name} - {self.date}"

    class Meta:
        verbose_name = "Plant & Equipment"
        verbose_name_plural = "Plant & Equipment"
        ordering = ["-date", "-created_at"]
