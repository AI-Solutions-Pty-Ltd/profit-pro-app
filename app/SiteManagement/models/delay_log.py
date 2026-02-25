"""Delay Log model for tracking project delays."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class DelayLog(BaseModel):
    """Track project delays and their impact."""

    class ClaimStatus(models.TextChoices):
        NOT_CLAIMED = "NOT_CLAIMED", "Not Claimed"
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="delay_logs",
        help_text="Project this delay log belongs to",
    )
    date = models.DateField(help_text="Date of delay")
    delay_description = models.TextField(help_text="Description of the delay")
    cause = models.TextField(help_text="Cause of the delay")
    impact = models.TextField(help_text="Impact of the delay")
    duration = models.PositiveIntegerField(help_text="Duration in days")
    claim_status = models.CharField(
        max_length=20,
        choices=ClaimStatus.choices,
        default=ClaimStatus.NOT_CLAIMED,
        help_text="Claim status",
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.delay_description[:50]} - {self.date}"

    class Meta:
        verbose_name = "Delay Log"
        verbose_name_plural = "Delay Logs"
        ordering = ["-date", "-created_at"]
