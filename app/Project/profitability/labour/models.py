from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.projects.projects_models import Project


class LabourCostTracker(BaseModel):
    """
    Labour cost tracking log for monitoring project expenditures.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="labour_cost_logs",
        help_text="Project this cost log belongs to",
    )
    labour_entity = models.ForeignKey(
        "Project.LabourEntity",
        on_delete=models.CASCADE,
        related_name="cost_logs",
        help_text="Link to master labour definition",
    )
    date = models.DateField(help_text="Date of monitoring")
    id_number = models.CharField(
        max_length=100, blank=True, help_text="Worker's ID number"
    )
    amount_of_days = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Amount of days worked"
    )
    salary = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Daily salary/rate"
    )

    @property
    def cost(self):
        """Calculate total labour cost."""
        return self.amount_of_days * self.salary

    def save(self, *args, **kwargs):
        """Auto-populate fields from linked entity if missing."""
        if self.labour_entity:
            if not self.id_number:
                self.id_number = self.labour_entity.id_number
            if self.salary == 0:
                self.salary = self.labour_entity.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.labour_entity.person_name} - {self.date} - {self.cost}"

    class Meta:
        verbose_name = "Labour Cost Tracker"
        verbose_name_plural = "Labour Cost Trackers"
        ordering = ["-date", "-created_at"]
