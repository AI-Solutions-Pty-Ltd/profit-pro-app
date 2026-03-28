"""Models for Planning & Procurement app.

Covers:
A) Work Packages - tender tracking with stage completion
B) Tender Documents - documentation linked to work packages
C) Design Development - engineering sketches/calculations at L1-L4 levels
"""

from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet

from app.Account.models import Account
from app.core.Utilities.models import BaseModel, sum_queryset
from app.Project.models import Category, Discipline, Group, Project, SubCategory

# =============================================================================
# A: Work Packages
# =============================================================================


class WorkPackage(BaseModel):
    """Work package representing a contract/tender being applied for.

    Tracks package dates across different stages and budget information.
    """

    class ContractType(models.TextChoices):
        """Contract type choices."""

        LUMP_SUM = "LUMP_SUM", "Lump Sum"
        BOQ = "BOQ", "BoQ"
        ACTIVITY_SCHEDULE = "ACTIVITY_SCHEDULE", "Activity Schedule"
        SCHEDULE_OF_RATES = "SCHEDULE_OF_RATES", "Schedule of Rates"
        OTHER = "OTHER", "Other - Specify"

    class ProcurementStrategy(models.TextChoices):
        """Procurement strategy choices."""

        SUPPLY = "SUPPLY", "Supply"
        INSTALL = "INSTALL", "Install"
        SUPPLY_AND_INSTALL = "SUPPLY_AND_INSTALL", "Supply & Install"

    class ConditionsOfContract(models.TextChoices):
        """Conditions of contract choices."""

        FIDIC = "FIDIC", "FIDIC"
        NEC = "NEC", "NEC"
        JBCC = "JBCC", "JBCC"
        CLIENT = "CLIENT", "Client"
        OTHER = "OTHER", "Other - Specify"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="work_packages",
        help_text="Project this work package belongs to",
    )
    package_number = models.CharField(
        max_length=256,
        blank=True,
        help_text="Package number/reference",
    )
    name = models.CharField(
        max_length=255,
        help_text="Name of the work package / contract",
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the work package",
    )
    contract_type = models.CharField(
        max_length=32,
        choices=ContractType.choices,
        blank=True,
        help_text="Type of contract",
    )
    procurement_strategy = models.CharField(
        max_length=32,
        choices=ProcurementStrategy.choices,
        blank=True,
        help_text="Procurement strategy",
    )
    conditions_of_contract = models.CharField(
        max_length=32,
        choices=ConditionsOfContract.choices,
        blank=True,
        help_text="Conditions of contract",
    )

    # Tender Milestones
    applied_to_advert_start_date = models.DateField(
        verbose_name="Advert Start Date",
        null=True,
        blank=True,
        help_text="Advert start date",
    )
    applied_to_advert_end_date = models.DateField(
        verbose_name="Advert End Date",
        null=True,
        blank=True,
        help_text="Advert end date",
    )
    applied_to_advert_completed = models.BooleanField(
        default=False,
        help_text="Whether applied to advert milestone is completed",
    )
    site_inspection_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Site inspection start date",
    )
    site_inspection_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Site inspection end date",
    )
    site_inspection_completed = models.BooleanField(
        default=False,
        help_text="Whether site inspection milestone is completed",
    )
    tender_close_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Tender close start date",
    )
    tender_close_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Tender close end date",
    )
    tender_close_completed = models.BooleanField(
        default=False,
        help_text="Whether tender close milestone is completed",
    )
    tender_evaluation_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Tender evaluation start date",
    )
    tender_evaluation_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Tender evaluation end date",
    )
    tender_evaluation_completed = models.BooleanField(
        default=False,
        help_text="Whether tender evaluation milestone is completed",
    )
    award_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Award start date",
    )
    award_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Award end date",
    )
    award_completed = models.BooleanField(
        default=False,
        help_text="Whether award milestone is completed",
    )
    contract_signing_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Contract signing start date",
    )
    contract_signing_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Contract signing end date",
    )
    contract_signing_completed = models.BooleanField(
        default=False,
        help_text="Whether contract signing milestone is completed",
    )
    mobilization_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Mobilization start date",
    )
    mobilization_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Mobilization end date",
    )
    mobilization_completed = models.BooleanField(
        default=False,
        help_text="Whether mobilization milestone is completed",
    )

    # Package Tracking Dates
    overall_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Overall package start date",
    )
    overall_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Overall package end/finish date",
    )
    documentation_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Documentation phase start date",
    )
    documentation_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Documentation phase end/finish date",
    )
    tender_process_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Tender process phase start date",
    )
    tender_process_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Tender process phase end/finish date",
    )
    execution_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Execution phase start date",
    )
    execution_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Execution phase end/finish date",
    )

    # Budget
    package_budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total package budget",
    )
    budget_structure_file = models.FileField(
        upload_to="planning/budget_structures/%Y/%m/",
        null=True,
        blank=True,
        help_text="Cost budget structure (sources of funds)",
    )

    if TYPE_CHECKING:
        tender_documents: QuerySet["TenderDocument"]

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Work Package"
        verbose_name_plural = "Work Packages"
        ordering = ["-created_at"]

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
            )

    def create_default_design_items(self) -> None:
        """Create design development items for all project categories/subcategories/groups/disciplines and both stages."""
        from app.Planning.models import (
            DesignCategory,
            DesignDiscipline,
            DesignGroup,
            DesignStage,
            DesignSubCategory,
        )

        # Create for both stages
        for stage in DesignStage.choices:
            stage_value = stage[0]

            # L1 - Categories
            for category in self.project.categories.all():
                DesignCategory.objects.get_or_create(
                    work_package=self,
                    category=category,
                    stage=stage_value,
                    defaults={"required_quantity": 1, "approved": False},
                )

            # L2 - SubCategories
            for subcategory in self.project.subcategories.all():
                DesignSubCategory.objects.get_or_create(
                    work_package=self,
                    sub_category=subcategory,
                    stage=stage_value,
                    defaults={"required_quantity": 1, "approved": False},
                )

            # L3 - Groups
            for group in self.project.groups.all():
                DesignGroup.objects.get_or_create(
                    work_package=self,
                    group=group,
                    stage=stage_value,
                    defaults={"required_quantity": 1, "approved": False},
                )

            # L4 - Disciplines
            for discipline in self.project.disciplines.all():
                DesignDiscipline.objects.get_or_create(
                    work_package=self,
                    discipline=discipline,
                    stage=stage_value,
                    defaults={"required_quantity": 1, "approved": False},
                )

    @property
    def total_tender_docs(self) -> int:
        """Return the total number of tender documents for this work package."""
        return int(sum_queryset(self.tender_documents, "required_quantity"))

    @property
    def completed_tender_docs(self) -> int:
        """Return the number of completed tender documents (those with files uploaded)."""
        count = 0
        for tender_document in self.tender_documents.all():
            count += tender_document.files.count()
        return count

    def save(self, *args, **kwargs) -> None:
        """Override save to auto-create design items and tender documents on creation."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.create_default_tender_documents()
            self.create_default_design_items()


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
    required_quantity = models.PositiveIntegerField(default=1)

    if TYPE_CHECKING:
        files: QuerySet["TenderDocumentFile"]

    def __str__(self) -> str:
        return f"{self.work_package.name} - {self.name}"

    class Meta:
        verbose_name = "Tender Document"
        verbose_name_plural = "Tender Documents"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["work_package", "name"],
                name="unique_tender_document_per_work_package",
            )
        ]

    @property
    def is_complete(self) -> bool:
        """A document category is complete when at least one file has been uploaded."""
        return self.progress == 100

    @property
    def file_count(self) -> int:
        """Return the number of files uploaded for this document."""
        return self.files.count()

    @property
    def progress(self) -> int:
        if self.required_quantity == 0:
            return 0
        return min(
            100, int(round((self.files.count() / self.required_quantity) * 100, 0))
        )


class TenderDocumentFile(BaseModel):
    """Individual file for a tender document."""

    tender_document = models.ForeignKey(
        TenderDocument,
        on_delete=models.CASCADE,
        related_name="files",
        help_text="Tender document this file belongs to",
    )
    file = models.FileField(
        upload_to="planning/tender_documents/",
        help_text="Uploaded tender document file",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the file was uploaded",
    )
    uploaded_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who uploaded the file",
    )

    def __str__(self) -> str:
        return f"{self.tender_document.name} - {self.file.name}"

    class Meta:
        verbose_name = "Tender Document File"
        verbose_name_plural = "Tender Document Files"
        ordering = ["-uploaded_at"]


# =============================================================================
# C: Design Development
# =============================================================================


class DesignStage(models.TextChoices):
    """Stages for design development documents."""

    DESIGN_CRITERIA = "DESIGN_CRITERIA", "Design Criteria"
    DRAWINGS = "DRAWINGS", "Drawings"
    DOCUMENTS = "DOCUMENTS", "Documents"


class DesignCategory(BaseModel):
    """Design development at L1 (Category) level.

    Linked to Category in project_models.py.
    """

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
    required_quantity = models.PositiveBigIntegerField(default=1)
    approved = models.BooleanField(
        default=False,
        help_text="Whether this design stage is approved",
    )

    if TYPE_CHECKING:
        files: QuerySet["DesignCategoryFile"]

    def __str__(self) -> str:
        return f"{self.category.name} - {self.get_stage_display()}"  # type: ignore

    class Meta:
        verbose_name = "Design Category (L1)"
        verbose_name_plural = "Design Categories (L1)"
        ordering = ["category__name", "stage"]

    @property
    def progress(self) -> int:
        if self.required_quantity == 0:
            return 0
        return min(
            100, int(round((self.files.count() / self.required_quantity) * 100, 0))
        )


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
    required_quantity = models.PositiveBigIntegerField(default=1)
    approved = models.BooleanField(
        default=False,
        help_text="Whether this design stage is approved",
    )

    if TYPE_CHECKING:
        files: QuerySet["DesignSubCategoryFile"]

    def __str__(self) -> str:
        return f"{self.sub_category.name} - {self.get_stage_display()}"  # type: ignore

    class Meta:
        verbose_name = "Design SubCategory (L2)"
        verbose_name_plural = "Design SubCategories (L2)"
        ordering = ["sub_category__name", "stage"]

    @property
    def progress(self) -> int:
        if self.required_quantity == 0:
            return 0
        return min(
            100, int(round((self.files.count() / self.required_quantity) * 100, 0))
        )


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
    required_quantity = models.PositiveBigIntegerField(default=1)
    approved = models.BooleanField(
        default=False,
        help_text="Whether this design stage is approved",
    )

    if TYPE_CHECKING:
        files: QuerySet["DesignGroupFile"]

    def __str__(self) -> str:
        return f"{self.group.name} - {self.get_stage_display()}"  # type: ignore

    class Meta:
        verbose_name = "Design Group (L3)"
        verbose_name_plural = "Design Groups (L3)"
        ordering = ["group__name", "stage"]

    @property
    def progress(self) -> int:
        if self.required_quantity == 0:
            return 0
        return min(
            100, int(round((self.files.count() / self.required_quantity) * 100, 0))
        )


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

    stage = models.CharField(
        max_length=30,
        choices=DesignStage.choices,
        default=DesignStage.DESIGN_CRITERIA,
        help_text="Current design stage",
    )
    discipline = models.ForeignKey(
        Discipline,
        on_delete=models.CASCADE,
        related_name="design_disciplines",
        help_text="L4 Discipline from project structure",
    )
    required_quantity = models.PositiveBigIntegerField(default=1)
    approved = models.BooleanField(
        default=False,
        help_text="Whether this design stage is approved",
    )

    if TYPE_CHECKING:
        files: QuerySet["DesignDisciplineFile"]

    def __str__(self) -> str:
        return f"{self.discipline.name} - {self.get_stage_display()}"  # type: ignore

    class Meta:
        verbose_name = "Design Discipline (L4)"
        verbose_name_plural = "Design Disciplines (L4)"
        ordering = ["discipline__name", "stage"]

    @property
    def progress(self) -> int:
        if self.required_quantity == 0:
            return 0
        return min(
            100, int(round((self.files.count() / self.required_quantity) * 100, 0))
        )


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
