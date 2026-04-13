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
    EARLY_WARNING = "EARLY_WARNING", "Early Warning"
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
    other_meeting_type = models.CharField(
        max_length=255,
        blank=True,
        help_text="Custom meeting type if 'Other' is selected",
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

    @property
    def decisions(self):
        """Return all decisions for this meeting."""
        return MeetingDecision.objects.filter(meeting=self)

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


class MeetingDecision(BaseModel):
    """Key decision made during a meeting."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="meeting_decisions",
        help_text="Meeting this decision belongs to",
    )
    description = models.TextField(
        help_text="Description of the decision made",
    )
    responsible_person = models.CharField(
        max_length=255,
        blank=True,
        help_text="Person responsible for this decision",
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date this decision/outcome is due",
    )

    def __str__(self):
        return f"Decision: {self.description[:50]}... ({self.meeting})"

    class Meta:
        verbose_name = "Meeting Decision"
        verbose_name_plural = "Meeting Decisions"
        ordering = ["created_at"]


class MeetingActionStatus(models.TextChoices):
    """Status choices for meeting actions."""

    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETE = "COMPLETE", "Complete"


class MeetingAction(BaseModel):
    """Action item linked to a meeting or a specific decision."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="meeting_actions",
        null=True,
        blank=True,
        help_text="Meeting this action belongs to",
    )
    decision = models.ForeignKey(
        MeetingDecision,
        on_delete=models.CASCADE,
        related_name="decision_actions",
        null=True,
        blank=True,
        help_text="Decision this action is linked to",
    )
    description = models.TextField(
        help_text="Action to be performed",
    )
    assigned_to = models.CharField(
        max_length=255,
        blank=True,
        help_text="Person responsible for this action",
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date this action is due",
    )
    status = models.CharField(
        max_length=20,
        choices=MeetingActionStatus.choices,
        default=MeetingActionStatus.PENDING,
        help_text="Current status of the action",
    )

    def __str__(self):
        return f"Action: {self.description[:50]}... ({self.status})"

    class Meta:
        verbose_name = "Meeting Action"
        verbose_name_plural = "Meeting Actions"
        ordering = ["due_date", "created_at"]
