from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.projects.projects_models import Project


class PlantCostTracker(BaseModel):
    """
    Plant and equipment cost tracking log for monitoring project expenditures.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="plant_cost_logs",
        help_text="Project this cost log belongs to",
    )
    plant_entity = models.ForeignKey(
        "Project.PlantEntity",
        on_delete=models.CASCADE,
        related_name="cost_logs",
        help_text="Link to master plant definition",
    )
    date = models.DateField(help_text="Date of usage")
    usage_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total usage hours",
    )
    hourly_rate = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Hourly rate"
    )
    breakdown_status = models.CharField(
        max_length=50,
        blank=True,
        help_text="Breakdown status during tracking",
    )
    maintenance_done = models.TextField(blank=True, help_text="Maintenance performed")
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    @property
    def cost(self):
        """Calculate total plant cost."""
        return self.usage_hours * self.hourly_rate

    def save(self, *args, **kwargs):
        """Auto-populate rate from linked entity's plant_type if not provided."""
        if self.plant_entity and self.hourly_rate == 0:
            if self.plant_entity.plant_type:
                self.hourly_rate = self.plant_entity.plant_type.hourly_rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.plant_entity.name} - {self.date} - ${self.cost}"

    class Meta:
        verbose_name = "Plant Cost Tracker"
        verbose_name_plural = "Plant Cost Trackers"
        ordering = ["-date", "-created_at"]
