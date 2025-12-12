"""Models for Contract Variations and Contractual Correspondences."""

from decimal import Decimal

from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel

# TYPE_CHECKING imports not needed - Project only used in string references


class ContractVariation(BaseModel):
    """
    Register of contract variations.

    Tracks changes to the original contract including time extensions
    and cost variations.
    """

    class Category(models.TextChoices):
        """Categories of contract variations."""

        SCOPE_CHANGE = "SCOPE_CHANGE", "Scope Change"
        DESIGN_CHANGE = "DESIGN_CHANGE", "Design Change"
        SITE_CONDITIONS = "SITE_CONDITIONS", "Unforeseen Site Conditions"
        CLIENT_REQUEST = "CLIENT_REQUEST", "Client Request"
        REGULATORY = "REGULATORY", "Regulatory Requirement"
        ERROR_OMISSION = "ERROR_OMISSION", "Error/Omission in Documents"
        FORCE_MAJEURE = "FORCE_MAJEURE", "Force Majeure"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        """Status of variation."""

        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class VariationType(models.TextChoices):
        """Type of variation - time or amount."""

        TIME = "TIME", "Time Extension"
        AMOUNT = "AMOUNT", "Cost Variation"
        BOTH = "BOTH", "Time and Cost"

    def upload_to(self, filename: str) -> str:
        """Generate upload path for attachments."""
        return f"contract_variations/{self.project.name}/{filename}"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="contract_variations",
        help_text="Project this variation belongs to",
    )
    variation_number = models.CharField(
        max_length=50,
        help_text="Unique variation reference number",
    )
    title = models.CharField(
        max_length=255,
        help_text="Brief title describing the variation",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of the variation",
    )
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
        help_text="Category of variation",
    )
    variation_type = models.CharField(
        max_length=20,
        choices=VariationType.choices,
        default=VariationType.AMOUNT,
        help_text="Whether this is a time, cost, or combined variation",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Current status of the variation",
    )

    # Time extension fields
    time_extension_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of days for time extension",
    )
    original_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Original project completion date before this variation",
    )
    revised_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Revised completion date after this variation",
    )

    # Cost variation fields
    variation_amount: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount of cost variation (positive for increase, negative for decrease)",
    )

    # Dates
    date_identified = models.DateField(
        null=True,
        blank=True,
        help_text="Date the variation was identified",
    )
    date_submitted = models.DateField(
        null=True,
        blank=True,
        help_text="Date variation was submitted for approval",
    )
    date_approved = models.DateField(
        null=True,
        blank=True,
        help_text="Date variation was approved",
    )

    # Approval tracking
    submitted_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_variations",
    )
    approved_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_variations",
    )

    # Attachment
    attachment = models.FileField(
        upload_to=upload_to,
        blank=True,
        null=True,
        help_text="Supporting documentation for the variation",
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes or comments",
    )

    class Meta:
        verbose_name = "Contract Variation"
        verbose_name_plural = "Contract Variations"
        ordering = ["-created_at"]
        unique_together = [["project", "variation_number"]]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return f"{self.variation_number}: {self.title}"

    def save(self, *args, **kwargs) -> None:
        """Override save to auto-generate variation number and handle status changes."""
        from datetime import date

        # Auto-generate variation number if not set
        if not self.variation_number:
            last_variation = (
                ContractVariation.objects.filter(project=self.project)
                .order_by("-created_at")
                .first()
            )
            if last_variation and last_variation.variation_number:
                # Extract number from last variation (e.g., "VAR-001" -> 1)
                try:
                    last_num = int(last_variation.variation_number.split("-")[-1])
                    self.variation_number = f"VAR-{last_num + 1:03d}"
                except (ValueError, IndexError):
                    self.variation_number = "VAR-001"
            else:
                self.variation_number = "VAR-001"

        # Auto-set date_submitted when status changes to SUBMITTED
        if self.status == self.Status.SUBMITTED and not self.date_submitted:
            self.date_submitted = date.today()

        # Auto-set date_approved when status changes to APPROVED
        if self.status == self.Status.APPROVED and not self.date_approved:
            self.date_approved = date.today()

        super().save(*args, **kwargs)

        # Update project dates/amounts when approved
        if self.status == self.Status.APPROVED:
            self._apply_variation_to_project()

    def _apply_variation_to_project(self) -> None:
        """Apply approved variation to project dates and amounts."""
        from dateutil.relativedelta import relativedelta

        project = self.project

        # Apply time extension to project completion date
        if self.variation_type in [self.VariationType.TIME, self.VariationType.BOTH]:
            if self.time_extension_days and project.revised_completion_date:
                project.approved_extension_days = (
                    project.approved_extension_days or 0
                ) + self.time_extension_days
                project.revised_completion_date = (
                    project.revised_completion_date
                    + relativedelta(days=self.time_extension_days)
                )
                project.save(
                    update_fields=["approved_extension_days", "revised_completion_date"]
                )


class ContractualCorrespondence(BaseModel):
    """
    Register of contractual correspondences.

    Tracks all formal communications related to the contract.
    """

    class CorrespondenceType(models.TextChoices):
        """Types of contractual correspondence."""

        LETTER = "LETTER", "Letter"
        EMAIL = "EMAIL", "Email"
        NOTICE = "NOTICE", "Formal Notice"
        INSTRUCTION = "INSTRUCTION", "Site Instruction"
        REQUEST = "REQUEST", "Request for Information"
        CLAIM = "CLAIM", "Claim Submission"
        RESPONSE = "RESPONSE", "Response"
        MEETING_MINUTES = "MEETING_MINUTES", "Meeting Minutes"
        REPORT = "REPORT", "Report"
        OTHER = "OTHER", "Other"

    class Direction(models.TextChoices):
        """Direction of correspondence."""

        INCOMING = "INCOMING", "Incoming"
        OUTGOING = "OUTGOING", "Outgoing"
        INTERNAL = "INTERNAL", "Internal"

    def upload_to(self, filename: str) -> str:
        """Generate upload path for attachments."""
        return f"contract_correspondences/{self.project.name}/{filename}"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="contractual_correspondences",
        help_text="Project this correspondence belongs to",
    )
    reference_number = models.CharField(
        max_length=100,
        help_text="Correspondence reference number",
    )
    subject = models.CharField(
        max_length=500,
        help_text="Subject of the correspondence",
    )
    correspondence_type = models.CharField(
        max_length=30,
        choices=CorrespondenceType.choices,
        default=CorrespondenceType.LETTER,
        help_text="Type of correspondence",
    )
    direction = models.CharField(
        max_length=20,
        choices=Direction.choices,
        default=Direction.OUTGOING,
        help_text="Direction of correspondence",
    )
    date_of_correspondence = models.DateField(
        help_text="Date of the correspondence",
    )
    date_received = models.DateField(
        null=True,
        blank=True,
        help_text="Date correspondence was received (for incoming)",
    )

    # Parties involved
    sender = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Name/organization of sender",
    )
    recipient = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Name/organization of recipient",
    )

    # Content
    summary = models.TextField(
        blank=True,
        default="",
        help_text="Brief summary of the correspondence content",
    )

    # Attachment
    attachment = models.FileField(
        upload_to=upload_to,
        blank=True,
        null=True,
        help_text="Attached document",
    )

    # Tracking
    requires_response = models.BooleanField(
        default=False,
        help_text="Whether this correspondence requires a response",
    )
    response_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Due date for response if required",
    )
    response_sent = models.BooleanField(
        default=False,
        help_text="Whether response has been sent",
    )
    response_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date response was sent",
    )

    # Linked correspondence
    related_correspondence = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="follow_up_correspondences",
        help_text="Related correspondence (e.g., original letter this responds to)",
    )

    # User tracking
    logged_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logged_correspondences",
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes",
    )

    class Meta:
        verbose_name = "Contractual Correspondence"
        verbose_name_plural = "Contractual Correspondences"
        ordering = ["-date_of_correspondence", "-created_at"]
        indexes = [
            models.Index(fields=["project", "correspondence_type"]),
            models.Index(fields=["date_of_correspondence"]),
            models.Index(fields=["requires_response", "response_sent"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number}: {self.subject}"
