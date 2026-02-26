"""Request for Information (RFI) model for contract management."""

import os

from django.db import models
from django.utils import timezone

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class RFIStatus(models.TextChoices):
    """Status choices for RFIs."""

    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class RFI(BaseModel):
    """Request for Information issued during contract management."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="rfis",
        help_text="Project this RFI belongs to",
    )
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Auto-generated reference number",
    )
    date_issued = models.DateField(
        auto_now_add=True,
        help_text="Date this RFI was issued",
    )
    issued_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        related_name="rfis_issued",
        editable=False,
        help_text="User who issued this RFI",
    )
    subject = models.CharField(
        max_length=255,
        help_text="Subject of the RFI",
    )
    message = models.TextField(
        help_text="Detailed description or question",
    )
    to_user = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rfis_received",
        help_text="User this RFI is addressed to",
    )

    def upload_to(self, filename):
        base_name = os.path.basename(filename)
        return f"rfis/attachments/{self.project.pk}/{base_name}"

    attachment = models.FileField(
        upload_to=upload_to,
        blank=True,
        null=True,
        help_text="Supporting attachment",
    )
    respond_by_date = models.DateField(
        help_text="Date by which a response is required",
    )
    response = models.TextField(
        blank=True,
        help_text="Response to this RFI",
    )
    response_attachment = models.FileField(
        upload_to="rfis/responses/",
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
        choices=RFIStatus.choices,
        default=RFIStatus.OPEN,
        help_text="Current status of this RFI",
    )
    date_closed = models.DateField(
        null=True,
        blank=True,
        editable=False,
        help_text="Date this RFI was closed (auto-set)",
    )

    def save(self, *args, **kwargs):
        """Auto-generate reference number and handle status timestamps."""
        if not self.reference_number:
            last = (
                RFI.objects.filter(project=self.project)
                .order_by("-created_at")
                .first()
            )
            count = (last.pk if last else 0) + 1 if last else 1
            self.reference_number = f"RFI-{self.project.pk:04d}-{count:04d}"

        if self.status == RFIStatus.CLOSED and not self.date_closed:
            self.date_closed = timezone.now().date()
        elif self.status == RFIStatus.OPEN:
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

    class Meta:
        verbose_name = "Request for Information"
        verbose_name_plural = "Requests for Information"
        ordering = ["-created_at"]
