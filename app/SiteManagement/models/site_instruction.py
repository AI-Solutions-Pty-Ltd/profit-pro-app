"""Site Instruction model for contract management."""

import os

from django.db import models
from django.utils import timezone

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class SiteInstructionStatus(models.TextChoices):
    """Status choices for site instructions."""

    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class SiteInstruction(BaseModel):
    """Site Instruction issued during contract management."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="site_instructions",
        help_text="Project this site instruction belongs to",
    )
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Auto-generated reference number",
    )
    date_notified = models.DateField(
        auto_now_add=True,
        help_text="Date this site instruction was issued",
    )
    issued_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        related_name="site_instructions_issued",
        editable=False,
        help_text="User who issued this site instruction",
    )
    subject = models.CharField(
        max_length=255,
        help_text="Subject of the site instruction",
    )
    instruction = models.TextField(
        help_text="Detailed instruction content",
    )
    to_user = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="site_instructions_received",
        help_text="User this instruction is addressed to",
    )

    def upload_to(self, filename):
        base_name = os.path.basename(filename)
        return f"site_instructions/attachments/{self.project.pk}/{base_name}"

    attachment = models.FileField(
        upload_to=upload_to,
        blank=True,
        null=True,
        help_text="Supporting attachment",
    )
    status = models.CharField(
        max_length=10,
        choices=SiteInstructionStatus.choices,
        default=SiteInstructionStatus.OPEN,
        help_text="Current status of this site instruction",
    )
    date_closed = models.DateField(
        null=True,
        blank=True,
        editable=False,
        help_text="Date this instruction was closed (auto-set)",
    )

    def save(self, *args, **kwargs):
        """Auto-generate reference number and handle status timestamps."""
        if not self.reference_number:
            last = (
                SiteInstruction.objects.filter(project=self.project)
                .order_by("-created_at")
                .first()
            )
            count = (last.pk if last else 0) + 1 if last else 1
            self.reference_number = f"SI-{self.project.pk:04d}-{count:04d}"

        if self.status == SiteInstructionStatus.CLOSED and not self.date_closed:
            self.date_closed = timezone.now().date()
        elif self.status == SiteInstructionStatus.OPEN:
            self.date_closed = None

        if not self.pk and self.attachment:
            attachment = self.attachment
            self.attachment = None
            super().save(*args, **kwargs)
            self.attachment = attachment

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_number} - {self.subject}"

    class Meta:
        verbose_name = "Site Instruction"
        verbose_name_plural = "Site Instructions"
        ordering = ["-created_at"]
