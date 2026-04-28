from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel


class ProjectReportSummary(BaseModel):
    """
    Model to store periodic report metadata, summaries, and recommendations.
    This allows Project Managers to provide qualitative data for reports.
    """

    project = models.ForeignKey(
        "Project.Project", on_delete=models.CASCADE, related_name="report_summaries"
    )
    period_start = models.DateField()
    period_end = models.DateField()

    # Construction Progress Report Fields
    project_status_summary = models.TextField(
        blank=True, help_text="Overall status of the project for this period"
    )
    key_achievements = models.TextField(
        blank=True, help_text="Major achievements during this period"
    )
    current_focus = models.TextField(
        blank=True, help_text="Current areas of focus for the next period"
    )
    hsq_summary = models.TextField(
        blank=True, help_text="Health, Safety, and Quality summary"
    )
    recommendations = models.TextField(
        blank=True, help_text="Recommendations for the project"
    )

    # Contractor's Report Specific Fields
    contractor_summary = models.TextField(
        blank=True, help_text="Contractor's summary of work and concerns"
    )

    created_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_report_summaries",
    )

    class Meta:
        verbose_name = "Project Report Summary"
        verbose_name_plural = "Project Report Summaries"
        unique_together = ("project", "period_start", "period_end")
        ordering = ["-period_end"]

    def __str__(self):
        return f"{self.project.name} Report Summary ({self.period_start} to {self.period_end})"
