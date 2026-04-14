"""Plant and Equipment model for tracking equipment usage."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project

from .plant_type import PlantType


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
    plant_type = models.ForeignKey(
        PlantType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="equipment_items",
        help_text="Type of plant/equipment",
    )
    plant_entity = models.ForeignKey(
        "Project.PlantEntity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plant_logs",
        help_text="Link to master plant definition",
    )
    date = models.DateField(help_text="Date of record")
    equipment_name = models.CharField(
        max_length=255,
        blank=True,
        editable=False,
        help_text="Specific equipment name/ID (optional)",
    )
    supplier = models.CharField(
        max_length=255, blank=True, editable=False, help_text="Supplier/Owner"
    )
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

    def save(self, *args, **kwargs):
        """Synchronize fields from master entity if linked."""
        if self.plant_entity:
            if not self.equipment_name:
                self.equipment_name = self.plant_entity.name
            if not self.supplier:
                self.supplier = self.plant_entity.supplier
            if not self.plant_type:
                self.plant_type = self.plant_entity.plant_type
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.equipment_name or (self.plant_type.name if self.plant_type else 'Equipment')} - {self.date}"

    @property
    def total_cost(self):
        """Calculate total cost based on the linked plant type's hourly rate."""
        if self.plant_type and self.usage_hours:
            return self.plant_type.hourly_rate * self.usage_hours
        return 0

    class Meta:
        verbose_name = "Plant & Equipment"
        verbose_name_plural = "Plant & Equipment"
        ordering = ["-date", "-created_at"]
