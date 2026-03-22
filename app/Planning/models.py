"""Models for Planning & Procurement app.

Covers:
A) Work Packages - tender tracking with stage completion
B) Tender Documents - documentation linked to work packages
C) Design Development - engineering sketches/calculations at L1-L4 levels
"""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import (
    Category,
    Discipline,
    Group,
    Project,
    SubCategory,
)

# =============================================================================
# A: Work Packages
# =============================================================================


class WorkPackage(BaseModel):
    """Work package representing a contract/tender being applied for.

    Tracks the tender lifecycle from advert through to mobilization,
    with percentage completion and boolean flags for each stage.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="work_packages",
        help_text="Project this work package belongs to",
    )
    name = models.CharField(
        max_length=255,
        help_text="Name of the work package / contract",
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the work package",
    )

    # Applied to Advert
    advert_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Advert start date",
    )
    advert_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Advert end date",
    )

    # Site Inspection
    site_inspection_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Site inspection completion percentage",
    )
    site_inspection_complete = models.BooleanField(
        default=False,
        help_text="Whether site inspection is complete",
    )

    # Tender Close
    tender_close_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Tender close completion percentage",
    )
    tender_close_complete = models.BooleanField(
        default=False,
        help_text="Whether tender close is complete",
    )

    # Tender Evaluation
    tender_evaluation_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Tender evaluation completion percentage",
    )
    tender_evaluation_complete = models.BooleanField(
        default=False,
        help_text="Whether tender evaluation is complete",
    )

    # Award & Contract Signing
    award_signing_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Award & contract signing completion percentage",
    )
    award_signing_complete = models.BooleanField(
        default=False,
        help_text="Whether award & contract signing is complete",
    )

    # Mobilization
    mobilization_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Mobilization completion percentage",
    )
    mobilization_complete = models.BooleanField(
        default=False,
        help_text="Whether mobilization is complete",
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Work Package"
        verbose_name_plural = "Work Packages"
        ordering = ["-created_at"]

    @property
    def overall_percentage(self) -> float:
        """Calculate overall completion percentage across all stages."""
        stages = [
            self.site_inspection_percentage,
            self.tender_close_percentage,
            self.tender_evaluation_percentage,
            self.award_signing_percentage,
            self.mobilization_percentage,
        ]
        return float(sum(stages) / len(stages))

    def create_default_tender_documents(self) -> None:
        """Create default tender documents for this work package."""
        defaults = [
            "L1 Bill of Quantities",
            "Specification",
            "Drawings",
            "Conditions of Contract",
            "Scope of Work",
        ]
        for name in defaults:
            TenderDocument.objects.get_or_create(
                work_package=self,
                name=name,
                defaults={"percentage_completed": 0},
            )


# =============================================================================
# B: Tender Documents
# =============================================================================


class TenderDocument(BaseModel):
    """Tender documentation linked to a work package.

    Each upload deems the category as complete.
    Tracks planned vs actual across planning activities.
    """

    work_package = models.ForeignKey(
        WorkPackage,
        on_delete=models.CASCADE,
        related_name="tender_documents",
        help_text="Work package this document belongs to",
    )
    name = models.CharField(
        max_length=255,
        help_text="Document category name",
    )
    file = models.FileField(
        upload_to="planning/tender_documents/",
        null=True,
        blank=True,
        help_text="Uploaded tender document file",
    )
    percentage_completed = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Completion percentage for this document category",
    )
    planned_date = models.DateField(
        null=True,
        blank=True,
        help_text="Planned completion date",
    )
    actual_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual completion date",
    )

    def __str__(self) -> str:
        return f"{self.work_package.name} - {self.name}"

    class Meta:
        verbose_name = "Tender Document"
        verbose_name_plural = "Tender Documents"
        ordering = ["name"]
        unique_together = [("work_package", "name")]

    @property
    def is_complete(self) -> bool:
        """A document category is complete when a file has been uploaded."""
        return bool(self.file)

    def save(self, *args, **kwargs) -> None:
        """Auto-set percentage to 100 if file is uploaded."""
        if self.file and self.percentage_completed == 0:
            self.percentage_completed = 100
        super().save(*args, **kwargs)


# =============================================================================
# C: Design Development
# =============================================================================


class DesignStage(models.TextChoices):
    """Stages for design development documents."""

    DESIGN_CRITERIA = "DESIGN_CRITERIA", "Design Criteria"
    DESIGN_CALCULATIONS = "DESIGN_CALCULATIONS", "Design Calculations"
    SKETCHES = "SKETCHES", "Sketches"


class DesignCategory(BaseModel):
    """Design development at L1 (Category) level.

    Linked to Category in project_models.py.
    """

    work_package = models.ForeignKey(
        WorkPackage,
        on_delete=models.CASCADE,
        related_name="design_categories",
        help_text="Work package this design category belongs to",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="design_categories",
        help_text="L1 Category from project structure",
    )
    stage = models.CharField(
        max_length=30,
        choices=DesignStage.choices,
        default=DesignStage.DESIGN_CRITERIA,
        help_text="Current design stage",
    )
    approved = models.BooleanField(
        default=False,
        help_text="Whether this design stage is approved",
    )

    def __str__(self) -> str:
        return f"{self.category.name} - {self.get_stage_display()}"  # type: ignore

    class Meta:
        verbose_name = "Design Category (L1)"
        verbose_name_plural = "Design Categories (L1)"
        ordering = ["category__name", "stage"]


class DesignCategoryFile(BaseModel):
    """File uploads for DesignCategory. Each upload deems the stage APPROVED."""

    design_category = models.ForeignKey(
        DesignCategory,
        on_delete=models.CASCADE,
        related_name="files",
        help_text="Design category this file belongs to",
    )
    file = models.FileField(
        upload_to="planning/design/category/",
        help_text="Uploaded design file",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Description of the uploaded file",
    )

    def __str__(self) -> str:
        return f"{self.design_category} - {self.file.name}"

    class Meta:
        verbose_name = "Design Category File"
        verbose_name_plural = "Design Category Files"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs) -> None:
        """Auto-approve the design category when a file is uploaded."""
        super().save(*args, **kwargs)
        if self.file and not self.design_category.approved:
            self.design_category.approved = True
            self.design_category.save(update_fields=["approved"])


class DesignSubCategory(BaseModel):
    """Design development at L2 (SubCategory) level.

    Linked to SubCategory in project_models.py.
    """

    work_package = models.ForeignKey(
        WorkPackage,
        on_delete=models.CASCADE,
        related_name="design_subcategories",
        help_text="Work package this design subcategory belongs to",
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name="design_subcategories",
        help_text="L2 SubCategory from project structure",
    )
    stage = models.CharField(
        max_length=30,
        choices=DesignStage.choices,
        default=DesignStage.DESIGN_CRITERIA,
        help_text="Current design stage",
    )
    approved = models.BooleanField(
        default=False,
        help_text="Whether this design stage is approved",
    )

    def __str__(self) -> str:
        return f"{self.sub_category.name} - {self.get_stage_display()}"  # type: ignore

    class Meta:
        verbose_name = "Design SubCategory (L2)"
        verbose_name_plural = "Design SubCategories (L2)"
        ordering = ["sub_category__name", "stage"]


class DesignSubCategoryFile(BaseModel):
    """File uploads for DesignSubCategory. Each upload deems the stage APPROVED."""

    design_sub_category = models.ForeignKey(
        DesignSubCategory,
        on_delete=models.CASCADE,
        related_name="files",
        help_text="Design subcategory this file belongs to",
    )
    file = models.FileField(
        upload_to="planning/design/subcategory/",
        help_text="Uploaded design file",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Description of the uploaded file",
    )

    def __str__(self) -> str:
        return f"{self.design_sub_category} - {self.file.name}"

    class Meta:
        verbose_name = "Design SubCategory File"
        verbose_name_plural = "Design SubCategory Files"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs) -> None:
        """Auto-approve the design subcategory when a file is uploaded."""
        super().save(*args, **kwargs)
        if self.file and not self.design_sub_category.approved:
            self.design_sub_category.approved = True
            self.design_sub_category.save(update_fields=["approved"])


class DesignGroup(BaseModel):
    """Design development at L3 (Group) level.

    Linked to Group in project_models.py.
    """

    work_package = models.ForeignKey(
        WorkPackage,
        on_delete=models.CASCADE,
        related_name="design_groups",
        help_text="Work package this design group belongs to",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="design_groups",
        help_text="L3 Group from project structure",
    )
    stage = models.CharField(
        max_length=30,
        choices=DesignStage.choices,
        default=DesignStage.DESIGN_CRITERIA,
        help_text="Current design stage",
    )
    approved = models.BooleanField(
        default=False,
        help_text="Whether this design stage is approved",
    )

    def __str__(self) -> str:
        return f"{self.group.name} - {self.get_stage_display()}"  # type: ignore

    class Meta:
        verbose_name = "Design Group (L3)"
        verbose_name_plural = "Design Groups (L3)"
        ordering = ["group__name", "stage"]


class DesignGroupFile(BaseModel):
    """File uploads for DesignGroup. Each upload deems the stage APPROVED."""

    design_group = models.ForeignKey(
        DesignGroup,
        on_delete=models.CASCADE,
        related_name="files",
        help_text="Design group this file belongs to",
    )
    file = models.FileField(
        upload_to="planning/design/group/",
        help_text="Uploaded design file",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Description of the uploaded file",
    )

    def __str__(self) -> str:
        return f"{self.design_group} - {self.file.name}"

    class Meta:
        verbose_name = "Design Group File"
        verbose_name_plural = "Design Group Files"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs) -> None:
        """Auto-approve the design group when a file is uploaded."""
        super().save(*args, **kwargs)
        if self.file and not self.design_group.approved:
            self.design_group.approved = True
            self.design_group.save(update_fields=["approved"])


class DesignDiscipline(BaseModel):
    """Design development at L4 (Discipline) level.

    Linked to Discipline in project_models.py.
    """

    work_package = models.ForeignKey(
        WorkPackage,
        on_delete=models.CASCADE,
        related_name="design_disciplines",
        help_text="Work package this design discipline belongs to",
    )
    discipline = models.ForeignKey(
        Discipline,
        on_delete=models.CASCADE,
        related_name="design_disciplines",
        help_text="L4 Discipline from project structure",
    )
    stage = models.CharField(
        max_length=30,
        choices=DesignStage.choices,
        default=DesignStage.DESIGN_CRITERIA,
        help_text="Current design stage",
    )
    approved = models.BooleanField(
        default=False,
        help_text="Whether this design stage is approved",
    )

    def __str__(self) -> str:
        return f"{self.discipline.name} - {self.get_stage_display()}"  # type: ignore

    class Meta:
        verbose_name = "Design Discipline (L4)"
        verbose_name_plural = "Design Disciplines (L4)"
        ordering = ["discipline__name", "stage"]


class DesignDisciplineFile(BaseModel):
    """File uploads for DesignDiscipline. Each upload deems the stage APPROVED."""

    design_discipline = models.ForeignKey(
        DesignDiscipline,
        on_delete=models.CASCADE,
        related_name="files",
        help_text="Design discipline this file belongs to",
    )
    file = models.FileField(
        upload_to="planning/design/discipline/",
        help_text="Uploaded design file",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Description of the uploaded file",
    )

    def __str__(self) -> str:
        return f"{self.design_discipline} - {self.file.name}"

    class Meta:
        verbose_name = "Design Discipline File"
        verbose_name_plural = "Design Discipline Files"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs) -> None:
        """Auto-approve the design discipline when a file is uploaded."""
        super().save(*args, **kwargs)
        if self.file and not self.design_discipline.approved:
            self.design_discipline.approved = True
            self.design_discipline.save(update_fields=["approved"])
