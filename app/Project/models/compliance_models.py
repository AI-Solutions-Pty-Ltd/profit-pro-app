"""Models for Compliance Management.

This module contains models for tracking contractor, consultant and client
performance against their contractual obligations.
"""

from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel


class ContractualCompliance(BaseModel):
    """
    Register of contractual obligations per contractor/consultant.

    Used to track project compliance during execution with due dates,
    frequency of activities and expiry dates where applicable.
    """

    class Frequency(models.TextChoices):
        """Frequency choices for compliance activities."""

        ONCE = "ONCE", "Once-off"
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        FORTNIGHTLY = "FORTNIGHTLY", "Fortnightly"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        ANNUALLY = "ANNUALLY", "Annually"
        AS_REQUIRED = "AS_REQUIRED", "As Required"

    class Status(models.TextChoices):
        """Status choices for compliance items."""

        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        OVERDUE = "OVERDUE", "Overdue"
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="contractual_compliance_items",
        help_text="Project this compliance item belongs to",
    )
    responsible_party = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractual_compliance_responsibilities",
        help_text="Contractor or consultant responsible for this obligation",
    )
    obligation_description = models.CharField(
        max_length=500,
        help_text="Description of the contractual obligation",
    )
    contract_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Reference to contract clause or section",
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Due date for this obligation",
    )
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.ONCE,
        help_text="Frequency of this compliance activity",
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expiry date where applicable",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Current status of this compliance item",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes about this compliance item",
    )
    created_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_contractual_compliance_items",
        help_text="User who created this compliance item",
    )

    class Meta:
        verbose_name = "Contractual Compliance"
        verbose_name_plural = "Contractual Compliance Items"
        ordering = ["due_date", "-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["responsible_party"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.obligation_description[:50]} - {self.get_status_display()}"  # type: ignore

    @property
    def is_overdue(self) -> bool:
        """Check if this compliance item is overdue."""
        from django.utils import timezone

        if self.due_date and self.status not in [
            self.Status.COMPLETED,
            self.Status.NOT_APPLICABLE,
        ]:
            return self.due_date < timezone.now().date()
        return False


class AdministrativeCompliance(BaseModel):
    """
    Track adherence to submission and approval timelines.

    Used for tracking certificates, forecasts, variations and correspondences.
    """

    class ItemType(models.TextChoices):
        """Types of administrative compliance items."""

        CERTIFICATE = "CERTIFICATE", "Certificate"
        FORECAST = "FORECAST", "Forecast"
        VARIATION = "VARIATION", "Variation"
        CORRESPONDENCE = "CORRESPONDENCE", "Correspondence"
        INSTRUCTION = "INSTRUCTION", "Site Instruction"
        CLAIM = "CLAIM", "Claim"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        """Status choices for administrative compliance."""

        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        OVERDUE = "OVERDUE", "Overdue"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="administrative_compliance_items",
        help_text="Project this compliance item belongs to",
    )
    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        help_text="Type of administrative item",
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Reference number for this item",
    )
    description = models.CharField(
        max_length=500,
        help_text="Description of the item",
    )
    responsible_party = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="administrative_compliance_responsibilities",
        help_text="Person responsible for this item",
    )
    submission_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Due date for submission",
    )
    submission_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual submission date",
    )
    approval_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Due date for approval",
    )
    approval_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual approval date",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Current status",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes",
    )
    created_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_administrative_compliance_items",
        help_text="User who created this item",
    )

    class Meta:
        verbose_name = "Administrative Compliance"
        verbose_name_plural = "Administrative Compliance Items"
        ordering = ["submission_due_date", "-created_at"]
        indexes = [
            models.Index(fields=["project", "item_type"]),
            models.Index(fields=["project", "status"]),
            models.Index(fields=["submission_due_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_item_type_display()}: {self.description[:50]}"  # type: ignore

    @property
    def is_submission_overdue(self) -> bool:
        """Check if submission is overdue."""
        from django.utils import timezone

        if self.submission_due_date and not self.submission_date:
            return self.submission_due_date < timezone.now().date()
        return False

    @property
    def is_approval_overdue(self) -> bool:
        """Check if approval is overdue."""
        from django.utils import timezone

        if self.approval_due_date and self.submission_date and not self.approval_date:
            return self.approval_due_date < timezone.now().date()
        return False


class FinalAccountCompliance(BaseModel):
    """
    Register of documents required for final handover documentation.

    Tracks documents, manuals, certificates, tests, etc. required
    as part of the final handover documentation.
    """

    class DocumentType(models.TextChoices):
        """Types of final account documents."""

        AS_BUILT_DRAWINGS = "AS_BUILT_DRAWINGS", "As-Built Drawings"
        OPERATION_MANUAL = "OPERATION_MANUAL", "Operation & Maintenance Manual"
        WARRANTY_CERTIFICATE = "WARRANTY_CERTIFICATE", "Warranty Certificate"
        TEST_CERTIFICATE = "TEST_CERTIFICATE", "Test Certificate"
        COMPLIANCE_CERTIFICATE = "COMPLIANCE_CERTIFICATE", "Compliance Certificate"
        OCCUPANCY_CERTIFICATE = "OCCUPANCY_CERTIFICATE", "Occupancy Certificate"
        TRAINING_RECORD = "TRAINING_RECORD", "Training Record"
        SPARE_PARTS_LIST = "SPARE_PARTS_LIST", "Spare Parts List"
        GUARANTEE = "GUARANTEE", "Guarantee"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        """Status choices for final account documents."""

        REQUIRED = "REQUIRED", "Required"
        REQUESTED = "REQUESTED", "Requested"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"

    def upload_to(self, filename: str) -> str:
        """Generate upload path for final account documents."""
        import os

        base_filename = os.path.basename(filename)
        return f"final_account_documents/{self.project.pk}/{base_filename}"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="final_account_compliance_items",
        help_text="Project this document belongs to",
    )
    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        help_text="Type of document",
    )
    description = models.CharField(
        max_length=500,
        help_text="Description of the document",
    )
    responsible_party = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="final_account_compliance_responsibilities",
        help_text="Person responsible for providing this document",
    )
    test_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of test/inspection where applicable",
    )
    submission_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date document was submitted",
    )
    approval_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date document was approved",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUIRED,
        help_text="Current status",
    )
    file = models.FileField(
        upload_to=upload_to,
        null=True,
        blank=True,
        help_text="Attached document file",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes",
    )
    created_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_final_account_compliance_items",
        help_text="User who created this item",
    )

    class Meta:
        verbose_name = "Final Account Compliance"
        verbose_name_plural = "Final Account Compliance Items"
        ordering = ["document_type", "-created_at"]
        indexes = [
            models.Index(fields=["project", "document_type"]),
            models.Index(fields=["project", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_document_type_display()}: {self.description[:50]}"  # type: ignore[attr-defined]

    @property
    def filename(self) -> str:
        """Return just the filename without the path."""
        if self.file:
            return self.file.name.split("/")[-1]
        return ""
