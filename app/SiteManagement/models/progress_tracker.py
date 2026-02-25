"""Progress Tracker model for tracking activity progress."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class ProgressTracker(BaseModel):
    """Track progress of project activities."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="progress_trackers",
        help_text="Project this progress tracker belongs to",
    )
    activity = models.CharField(max_length=255, help_text="Activity name")
    planned_start_date = models.DateField(help_text="Planned start date")
    planned_end_date = models.DateField(help_text="Planned end date")
    actual_start_date = models.DateField(
        blank=True, null=True, help_text="Actual start date"
    )
    actual_end_date = models.DateField(
        blank=True, null=True, help_text="Actual end date"
    )
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage completion (0-100)",
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.activity} - {self.completion_percentage}%"

    class Meta:
        verbose_name = "Progress Tracker"
        verbose_name_plural = "Progress Trackers"
        ordering = ["planned_start_date", "-created_at"]
