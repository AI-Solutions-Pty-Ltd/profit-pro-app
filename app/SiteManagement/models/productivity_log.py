"""Productivity Log model for tracking work output."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class ProductivityLog(BaseModel):
    """Track productivity metrics for tasks."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="productivity_logs",
        help_text="Project this productivity log belongs to",
    )
    date = models.DateField(help_text="Date of work")
    task = models.CharField(max_length=255, help_text="Task description")
    crew_size = models.PositiveIntegerField(help_text="Number of workers")
    hours_worked = models.DecimalField(
        max_digits=6, decimal_places=2, help_text="Total hours worked"
    )
    output = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Output achieved"
    )
    output_unit = models.CharField(max_length=50, help_text="Unit of output")
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
        if self.output and self.hours_worked and self.hours_worked > 0:
            self.productivity = self.output / self.hours_worked
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.task} - {self.date}"

    class Meta:
        verbose_name = "Productivity Log"
        verbose_name_plural = "Productivity Logs"
        ordering = ["-date", "-created_at"]
