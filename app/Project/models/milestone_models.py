"""Milestone model for Time Forecast feature."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project, Category, SubCategory, Discipline


class Milestone(BaseModel):
    """Project milestone for time forecast tracking.

    Tracks planned vs forecast completion times for key project milestones.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="milestones",
        help_text="Project this milestone belongs to",
    )
    name = models.CharField(
        max_length=255,
        help_text="Milestone name/description",
    )
    planned_date = models.DateField(
        help_text="Original planned/baseline completion date",
    )
    forecast_date = models.DateField(
        null=True,
        blank=True,
        help_text="Current forecast completion date",
    )
    reason_for_change = models.TextField(
        blank=True,
        help_text="Reason for change in forecast date",
    )
    sequence = models.PositiveIntegerField(
        default=0,
        help_text="Order of milestone in project timeline",
    )
    is_completed = models.BooleanField(
        default=False,
        help_text="Whether this milestone has been completed",
    )
    actual_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual completion date (when completed)",
    )
    project_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="milestones",
        help_text="WBS Level 1 classification",
    )
    project_category_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Start date for WBS Level 1",
    )
    project_category_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date for WBS Level 1",
    )
    project_sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="milestones",
        help_text="WBS Level 2 classification",
    )
    project_sub_category_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Start date for WBS Level 2",
    )
    project_sub_category_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date for WBS Level 2",
    )
    project_discipline = models.ForeignKey(
        Discipline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="milestones",
        help_text="WBS Level 3 classification",
    )
    project_discipline_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Start date for WBS Level 3",
    )
    project_discipline_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date for WBS Level 3",
    )

    def __str__(self) -> str:
        return f"{self.project.name}: {self.name}"

    class Meta:
        verbose_name = "Milestone"
        verbose_name_plural = "Milestones"
        ordering = ["project", "sequence", "planned_date"]
        unique_together = [["project", "name"]]

    @property
    def variance_days(self) -> int | None:
        """Calculate variance in days between planned and forecast dates.

        Returns:
            Positive value means delay, negative means ahead of schedule.
            None if forecast date is not set.
        """
        if not self.forecast_date:
            return None
        return (self.forecast_date - self.planned_date).days

    @property
    def is_delayed(self) -> bool:
        """Check if milestone is delayed."""
        variance = self.variance_days
        return variance is not None and variance > 0

    @property
    def is_ahead(self) -> bool:
        """Check if milestone is ahead of schedule."""
        variance = self.variance_days
        return variance is not None and variance < 0

    @property
    def status(self) -> str:
        """Get milestone status as string."""
        if self.is_completed:
            return "Completed"
        variance = self.variance_days
        if variance is None:
            return "Pending Forecast"
        if variance > 0:
            return f"Delayed ({variance} days)"
        elif variance < 0:
            return f"Ahead ({abs(variance)} days)"
        return "On Schedule"
