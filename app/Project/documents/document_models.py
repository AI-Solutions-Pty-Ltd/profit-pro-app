"""Models for Project Documents and Contract Records."""

from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
from app.Project.projects.projects_models import (
    Category,
    Discipline,
    SubCategory,
)


class ProjectDocument(BaseModel):
    """
    Generic document storage for project-related files.

    Used for storing contract documents, appointment letters,
    stage gate approvals, and other audit-required documentation.
    """

    class DocumentCategory(models.TextChoices):
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
        BILL_OF_QUANTITIES = "BILL_OF_QUANTITIES", "Bill of Quantities"
        APPOINTMENT_LETTER = "APPOINTMENT_LETTER", "Appointment Letter"
        FINANCIAL_DOCUMENTS = "FINANCIAL_DOCUMENTS", "Financial Documents"
        MEETING_MINUTES = "MEETING_MINUTES", "Meeting Minutes"
        GENERAL_CORRESPONDENCE = "GENERAL_CORRESPONDENCE", "General Correspondence"
        REPORTS = "REPORTS", "Reports"
        PERMITS_APPROVALS = "PERMITS_APPROVALS", "Permits & Approvals"
        PHOTOS_IMAGES = "PHOTOS_IMAGES", "Photos & Images"
        OTHER = "OTHER", "Other"
        DRAWINGS = "DRAWINGS", "Drawings"
        SPECIFICATIONS = "SPECIFICATIONS", "Specifications"
        HISTORIC_DOCUMENTS = "HISTORIC_DOCUMENTS", "Historic Documents"
        CONTRACTUAL_PROGRAMME = "CONTRACTUAL_PROGRAMME", "Contractual Programme"

    def upload_to(self, filename: str) -> str:
        """Generate upload path for document files."""
        import os

        base_filename = os.path.basename(filename)
        return f"project_documents/{self.project.pk}/{self.category}/{base_filename}"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Project this document belongs to",
    )
    category = models.CharField(
        max_length=30,
        choices=DocumentCategory.choices,
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

    project_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Project category (e.g., Education, Health, Roads)",
    )
    area = models.ForeignKey(
        "Account.Municipality",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Project area (Municipality)",
    )
    project_discipline = models.ForeignKey(
        Discipline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Project discipline",
    )

    def __str__(self) -> str:
        return f"{self.title} ({self.get_category_display()})"  # type: ignore

    @property
    def filename(self) -> str:
        """Return just the filename without the path."""
        if self.file and self.file.name:
            return self.file.name.split("/")[-1]
        return self.pk


class Drawing(BaseModel):
    """
    Dedicated model for project drawings.

    Supports nested hierarchy, revision tracking, and integration
    with project disciplines and WBS levels.
    """

    def upload_to(self, filename: str) -> str:
        """Generate upload path for drawing files."""
        import os

        base_filename = os.path.basename(filename)
        return f"project_drawings/{self.project.pk}/{self.discipline}/{base_filename}"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="drawings",
        help_text="Project this drawing belongs to",
    )
    drawing_number = models.CharField(
        max_length=100,
        help_text="Unique identifier for the drawing",
    )
    name = models.CharField(
        max_length=255,
        help_text="Title or name of the drawing",
    )
    revision_number = models.CharField(
        max_length=50,
        help_text="Current revision number (e.g., A, 01, Rev 1)",
    )
    discipline = models.ForeignKey(
        Discipline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drawings",
        help_text="Professional discipline this drawing belongs to",
    )

    # Hierarchy/Nesting
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text="Parent drawing for nested hierarchy",
    )

    # Link to WBS Levels
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drawings",
        help_text="Project category (Level 1)",
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drawings",
        help_text="Project sub-category (Level 2)",
    )

    file = models.FileField(
        upload_to=upload_to,
        help_text="The uploaded drawing file (PDF, CAD, etc.)",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes about the drawing",
    )

    class Meta:
        verbose_name = "Drawing"
        verbose_name_plural = "Drawings"
        ordering = ["drawing_number"]
        indexes = [
            models.Index(fields=["project", "drawing_number"]),
            models.Index(fields=["discipline"]),
        ]

    def __str__(self) -> str:
        return f"{self.drawing_number}: {self.name} (Rev {self.revision_number})"

    @property
    def level(self) -> int:
        """Calculate the depth level in the drawing hierarchy."""
        level = 0
        curr = self.parent
        while curr:
            level += 1
            curr = curr.parent
        return level

    @property
    def filename(self) -> str:
        """Return just the filename without the path."""
        if self.file and self.file.name:
            return self.file.name.split("/")[-1]
        return str(self.pk)
