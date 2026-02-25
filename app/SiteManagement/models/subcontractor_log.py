"""Subcontractor Log model for tracking subcontractor activities."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class SubcontractorLog(BaseModel):
    """Track subcontractor work and productivity."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="subcontractor_logs",
        help_text="Project this subcontractor log belongs to",
    )
    name = models.CharField(max_length=255, help_text="Subcontractor name")
    trade = models.CharField(max_length=100, help_text="Trade/specialty")
    scope = models.TextField(help_text="Scope of work")
    start_date = models.DateField(help_text="Start date")
    planned_finish_date = models.DateField(
        blank=True, null=True, help_text="Planned finish date"
    )
    actual_finish_date = models.DateField(
        blank=True, null=True, help_text="Actual finish date"
    )
    task = models.CharField(max_length=255, help_text="Current task")
    hours_worked = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Hours worked",
    )
    output = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Output achieved",
    )
    output_unit = models.CharField(
        max_length=50, blank=True, help_text="Unit of output"
    )
    productivity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Productivity (Output/Hour)",
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def save(self, *args, **kwargs):
        """Calculate productivity before saving."""
        if (
            self.output
            and self.hours_worked
            and self.hours_worked > 0
            and self.output is not None
        ):
            self.productivity = self.output / self.hours_worked
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.trade}"

    class Meta:
        verbose_name = "Subcontractor Log"
        verbose_name_plural = "Subcontractor Logs"
        ordering = ["-start_date", "-created_at"]
