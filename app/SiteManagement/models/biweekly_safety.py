"""Bi-Weekly Safety Report model."""

from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class BiWeeklySafetyReport(BaseModel):
    """Bi-weekly safety performance summary submitted by the contractor."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="biweekly_safety_reports",
        help_text="Project this report belongs to",
    )
    period_start = models.DateField(help_text="Start of the two-week period")
    period_end = models.DateField(help_text="End of the two-week period")
    submitted_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="submitted_safety_reports",
        help_text="User who submitted this report",
    )
    key_concerns = models.TextField(
        blank=True,
        help_text="Key safety concerns or observations for this period",
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes",
    )

    class Meta:
        verbose_name = "Bi-Weekly Safety Report"
        verbose_name_plural = "Bi-Weekly Safety Reports"
        ordering = ["-period_end", "-created_at"]

    def __str__(self) -> str:
        return f"Safety Report: {self.period_start} – {self.period_end} ({self.project})"
