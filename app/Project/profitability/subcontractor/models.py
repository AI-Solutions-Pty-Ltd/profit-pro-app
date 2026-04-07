from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.projects.projects_models import Project


class SubcontractorCostTracker(BaseModel):
    """
    Subcontractor cost tracking log for monitoring project expenditures.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="subcontractor_cost_logs",
        help_text="Project this cost log belongs to",
    )
    subcontractor_entity = models.ForeignKey(
        "Project.SubcontractorEntity",
        on_delete=models.CASCADE,
        related_name="cost_logs",
        help_text="Link to master subcontractor definition",
    )
    date = models.DateField(help_text="Date of monitoring")
    reference_no = models.CharField(
        max_length=100, blank=True, help_text="Reference number for the transaction"
    )
    amount_of_days = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Number of days/units tracked",
    )
    rate = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Rate per day/unit"
    )

    @property
    def cost(self):
        """Calculate total cost."""
        return self.amount_of_days * self.rate

    def save(self, *args, **kwargs):
        """Auto-populate fields from linked entity if missing."""
        if self.subcontractor_entity:
            if not self.reference_no:
                self.reference_no = self.subcontractor_entity.reference_no
            if self.rate == 0:
                self.rate = self.subcontractor_entity.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subcontractor_entity.name} - {self.date} - {self.cost}"

    class Meta:
        verbose_name = "Subcontractor Cost Tracker"
        verbose_name_plural = "Subcontractor Cost Trackers"
        ordering = ["-date", "-created_at"]
