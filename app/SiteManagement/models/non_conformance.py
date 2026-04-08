"""Non-Conformance Report (NCR) model for Safety and Quality tracking."""

import os

from django.db import models
from django.utils import timezone

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class NCRType(models.TextChoices):
    SAFETY = "SAFETY", "Safety"
    QUALITY = "QUALITY", "Quality"


class NCRStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class NonConformance(BaseModel):
    """Unified Non-Conformance Report for Safety and Quality NCRs."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="non_conformances",
        help_text="Project this NCR belongs to",
    )
    reference_number = models.CharField(
        max_length=50,
        editable=False,
        blank=True,
        help_text="Auto-generated reference number",
    )
    ncr_type = models.CharField(
        max_length=10,
        choices=NCRType.choices,
        default=NCRType.QUALITY,
        help_text="Type of non-conformance (Safety or Quality)",
    )
    date = models.DateField(
        auto_now_add=True,
        help_text="Date this NCR was raised",
    )
    description = models.TextField(
        help_text="Description of the non-conformance",
    )
    defect_description = models.TextField(
        blank=True,
        help_text="Detailed description of the defect (Quality NCRs)",
    )
    root_cause = models.TextField(
        blank=True,
        help_text="Root cause analysis",
    )
    responsible_person = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_ncrs",
        help_text="Person responsible for closing out this NCR",
    )
    corrective_action = models.TextField(
        blank=True,
        help_text="Corrective action issued",
    )
    preventative_action = models.TextField(
        blank=True,
        help_text="Preventative action to avoid recurrence",
    )
    status = models.CharField(
        max_length=10,
        choices=NCRStatus.choices,
        default=NCRStatus.OPEN,
        help_text="Current status of this NCR",
    )
    date_closed = models.DateField(
        null=True,
        blank=True,
        editable=False,
        help_text="Date this NCR was closed (auto-set)",
    )

    def _photo_upload_to(self, filename: str) -> str:
        base = os.path.basename(filename)
        return f"ncr_photos/{self.project_id}/{self.ncr_type}/{base}"

    photo = models.ImageField(
        upload_to=_photo_upload_to,
        blank=True,
        null=True,
        help_text="Photographic evidence",
    )

    class Meta:
        verbose_name = "Non-Conformance Report"
        verbose_name_plural = "Non-Conformance Reports"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "ncr_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number} – {self.get_ncr_type_display()} NCR ({self.status})"

    def save(self, *args, **kwargs) -> None:
        """Auto-generate reference number and handle close timestamp."""
        if not self.reference_number:
            prefix = "SNCR" if self.ncr_type == NCRType.SAFETY else "QNCR"
            count = (
                NonConformance.all_objects.filter(
                    project=self.project, ncr_type=self.ncr_type
                ).count()
                + 1
            )
            self.reference_number = f"{prefix}-{self.project.pk:04d}-{count:04d}"

        if self.status == NCRStatus.CLOSED and not self.date_closed:
            self.date_closed = timezone.now().date()
        elif self.status == NCRStatus.OPEN:
            self.date_closed = None

        super().save(*args, **kwargs)
