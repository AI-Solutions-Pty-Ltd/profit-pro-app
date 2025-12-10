"""Models for Project Documents and Contract Records."""

from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel


class ProjectDocument(BaseModel):
    """
    Generic document storage for project-related files.

    Used for storing contract documents, appointment letters,
    stage gate approvals, and other audit-required documentation.
    """

    class Category(models.TextChoices):
        """Categories of project documents."""

        CONTRACT_DOCUMENTS = (
            "CONTRACT_DOCUMENTS",
            "Contract Documents & Appointment Letters",
        )
        STAGE_GATE_APPROVAL = "STAGE_GATE_APPROVAL", "Stage Gate Approval Documentation"
        TECHNICAL_SPECIFICATIONS = (
            "TECHNICAL_SPECIFICATIONS",
            "Technical Specifications",
        )
        FINANCIAL_DOCUMENTS = "FINANCIAL_DOCUMENTS", "Financial Documents"
        MEETING_MINUTES = "MEETING_MINUTES", "Meeting Minutes"
        GENERAL_CORRESPONDENCE = "GENERAL_CORRESPONDENCE", "General Correspondence"
        REPORTS = "REPORTS", "Reports"
        PERMITS_APPROVALS = "PERMITS_APPROVALS", "Permits & Approvals"
        PHOTOS_IMAGES = "PHOTOS_IMAGES", "Photos & Images"
        OTHER = "OTHER", "Other"

    def upload_to(self, filename: str) -> str:
        """Generate upload path for document files."""
        return f"project_documents/{self.project_id}/{self.category}/{filename}"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Project this document belongs to",
    )
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        help_text="Category of the document",
    )
    title = models.CharField(
        max_length=255,
        help_text="Document title or description",
    )
    file = models.FileField(
        upload_to=upload_to,
        help_text="The uploaded document file",
    )
    uploaded_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_project_documents",
        help_text="User who uploaded this document",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes about the document",
    )

    class Meta:
        verbose_name = "Project Document"
        verbose_name_plural = "Project Documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "category"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_category_display()})"

    @property
    def filename(self) -> str:
        """Return just the filename without the path."""
        if self.file:
            return self.file.name.split("/")[-1]
        return ""
