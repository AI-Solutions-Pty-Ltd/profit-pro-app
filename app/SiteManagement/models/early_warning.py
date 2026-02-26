"""Early Warning model for contract management."""

import os

from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class EarlyWarningImpact(models.TextChoices):
    """Impact types for early warnings."""

    TIME = "TIME", "Time"
    COST = "COST", "Cost"
    QUALITY = "QUALITY", "Quality"


class EarlyWarningStatus(models.TextChoices):
    """Status choices for early warnings."""

    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class EarlyWarning(BaseModel):
    """Early Warning notice for contract management."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="early_warnings",
        help_text="Project this early warning belongs to",
    )
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Auto-generated reference number",
    )
    date = models.DateField(
        auto_now_add=True,
        help_text="Date this early warning was raised",
    )
    submitted_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        related_name="early_warnings_submitted",
        editable=False,
        help_text="User who submitted this early warning",
    )
    submitted_by_role = models.CharField(
        max_length=255,
        blank=True,
        editable=False,
        help_text="Role of the submitter at time of submission",
    )
    to_user = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        related_name="early_warnings_received",
        help_text="User this early warning is addressed to",
    )
    subject = models.CharField(
        max_length=255,
        help_text="Subject of the early warning",
    )
    message = models.TextField(
        help_text="Detailed description of the early warning",
    )
    impact_time = models.BooleanField(
        default=False,
        help_text="This warning impacts time",
    )
    impact_cost = models.BooleanField(
        default=False,
        help_text="This warning impacts cost",
    )
    impact_quality = models.BooleanField(
        default=False,
        help_text="This warning impacts quality",
    )
    respond_by_date = models.DateField(
        help_text="Date by which a response is required",
    )

    def upload_to(self, filename):
        base_name = os.path.basename(filename)
        return f"early_warnings/attachments/{self.project.pk}/{base_name}"

    attachment = models.FileField(
        upload_to=upload_to,
        blank=True,
        null=True,
        help_text="Supporting attachment from submitter",
    )
    response = models.TextField(
        blank=True,
        help_text="Response to this early warning",
    )
    response_attachment = models.FileField(
        upload_to="early_warnings/responses/",
        blank=True,
        null=True,
        help_text="Supporting attachment for response",
    )
    response_date = models.DateField(
        null=True,
        blank=True,
        editable=False,
        help_text="Date the response was submitted (auto-set)",
    )
    status = models.CharField(
        max_length=10,
        choices=EarlyWarningStatus.choices,
        default=EarlyWarningStatus.OPEN,
        help_text="Current status of this early warning",
    )
    date_closed = models.DateField(
        null=True,
        blank=True,
        editable=False,
        help_text="Date this early warning was closed (auto-set)",
    )

    def save(self, *args, **kwargs):
        """Auto-generate reference number and handle status timestamps."""
        from django.utils import timezone

        if not self.reference_number:
            last = (
                EarlyWarning.objects.filter(project=self.project)
                .order_by("-created_at")
                .first()
            )
            count = (last.pk if last else 0) + 1 if last else 1
            self.reference_number = f"EW-{self.project.pk:04d}-{count:04d}"

        if self.status == EarlyWarningStatus.CLOSED and not self.date_closed:
            self.date_closed = timezone.now().date()
        elif self.status == EarlyWarningStatus.OPEN:
            self.date_closed = None

        if self.response and not self.response_date:
            self.response_date = timezone.now().date()

        if not self.pk and self.attachment:
            attachment = self.attachment
            self.attachment = None
            super().save(*args, **kwargs)
            self.attachment = attachment

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_number} - {self.subject}"

    @property
    def from_display(self):
        """Display string for the submitter."""
        if self.submitted_by:
            name = self.submitted_by.get_full_name() or self.submitted_by.email
            role = self.submitted_by_role or "Contractor"
            return f"{name} ({role})"
        return "-"

    @property
    def impacts(self):
        """List of active impact types."""
        impacts = []
        if self.impact_time:
            impacts.append("Time")
        if self.impact_cost:
            impacts.append("Cost")
        if self.impact_quality:
            impacts.append("Quality")
        return impacts

    class Meta:
        verbose_name = "Early Warning"
        verbose_name_plural = "Early Warnings"
        ordering = ["-created_at"]
