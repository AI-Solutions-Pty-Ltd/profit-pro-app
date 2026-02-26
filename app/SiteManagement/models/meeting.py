"""Meeting model for contract management."""

import os

from django.db import models
from django.utils import timezone

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class MeetingType(models.TextChoices):
    """Type choices for meetings."""

    PROGRESS = "PROGRESS", "Progress"
    CONTRACTUAL = "CONTRACTUAL", "Contractual"
    RISK = "RISK", "Risk"
    OTHER = "OTHER", "Other"


class MeetingStatus(models.TextChoices):
    """Status choices for meetings."""

    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class Meeting(BaseModel):
    """Meeting record for a project."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="meetings",
        help_text="Project this meeting belongs to",
    )
    meeting_type = models.CharField(
        max_length=20,
        choices=MeetingType.choices,
        help_text="Type of meeting",
    )
    date = models.DateField(
        help_text="Date of the meeting",
    )
    key_decisions = models.TextField(
        blank=True,
        help_text="Key decisions made during the meeting",
    )

    def upload_to(self, filename):
        base_name = os.path.basename(filename)
        return f"meetings/attachments/{self.project.pk}/{base_name}"

    attachment = models.FileField(
        upload_to=upload_to,
        blank=True,
        null=True,
        help_text="Meeting minutes or other supporting documents",
    )
    status = models.CharField(
        max_length=10,
        choices=MeetingStatus.choices,
        default=MeetingStatus.OPEN,
        help_text="Current status of this meeting",
    )
    date_closed = models.DateField(
        null=True,
        blank=True,
        editable=False,
        help_text="Date this meeting was closed (auto-set)",
    )

    def save(self, *args, **kwargs):
        """Handle status timestamps and attachment on first save."""
        if self.status == MeetingStatus.CLOSED and not self.date_closed:
            self.date_closed = timezone.now().date()
        elif self.status == MeetingStatus.OPEN:
            self.date_closed = None

        if not self.pk and self.attachment:
            attachment = self.attachment
            self.attachment = None
            super().save(*args, **kwargs)
            self.attachment = attachment

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.meeting_type} Meeting - {self.date} ({self.project})"

    class Meta:
        verbose_name = "Meeting"
        verbose_name_plural = "Meetings"
        ordering = ["-date", "-created_at"]
