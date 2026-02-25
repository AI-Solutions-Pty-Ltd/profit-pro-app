"""Daily Diary model for tracking daily site activities."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class DailyDiary(BaseModel):
    """Track daily site activities and events."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="daily_diaries",
        help_text="Project this diary entry belongs to",
    )
    date = models.DateField(help_text="Date of diary entry")
    weather = models.CharField(max_length=100, help_text="Weather conditions")
    work_activities = models.TextField(help_text="Work activities performed")
    visitors = models.TextField(blank=True, help_text="Site visitors")
    issues_delays = models.TextField(
        blank=True, help_text="Issues or delays encountered"
    )
    site_instructions = models.TextField(
        blank=True, help_text="Site instructions given"
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"Daily Diary - {self.date}"

    class Meta:
        verbose_name = "Daily Diary"
        verbose_name_plural = "Daily Diaries"
        ordering = ["-date", "-created_at"]
