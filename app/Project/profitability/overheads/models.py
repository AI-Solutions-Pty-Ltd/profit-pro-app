from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.projects.projects_models import Project


class OverheadCostTracker(BaseModel):
    """
    Overhead cost tracking log for monitoring project expenditures.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="overhead_cost_logs",
        help_text="Project this cost log belongs to",
    )
    overhead_entity = models.ForeignKey(
        "Project.OverheadEntity",
        on_delete=models.CASCADE,
        related_name="cost_logs",
        help_text="Link to master overhead definition",
    )
    date = models.DateField(help_text="Date of monitoring")
    amount_of_days = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Amount of days tracked"
    )
    rate = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Daily rate/cost"
    )

    @property
    def cost(self):
        """Calculate total overhead cost."""
        return self.amount_of_days * self.rate

    def save(self, *args, **kwargs):
        """Auto-populate fields from linked entity if missing."""
        if self.overhead_entity:
            if self.rate == 0:
                self.rate = self.overhead_entity.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.overhead_entity.name} - {self.date} - {self.cost}"

    class Meta:
        verbose_name = "Overhead Cost Tracker"
        verbose_name_plural = "Overhead Cost Trackers"
        ordering = ["-date", "-created_at"]
