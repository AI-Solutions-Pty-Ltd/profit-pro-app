"""Project Entity Definitions for centralized resource management."""

from django.db import models

from app.core.Utilities.models import BaseModel


class BaseProjectEntity(BaseModel):
    """Abstract base model for all project-scoped entities."""

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="%(class)s_entities",
        help_text="Project this entity belongs to",
    )
    name = models.CharField(max_length=255, help_text="Entity name")
    reference_no = models.CharField(
        max_length=100, blank=True, unique=True, help_text="Unique reference number"
    )
    unit = models.CharField(max_length=50, blank=True, help_text="Unit of measure")
    rate = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Rate per unit"
    )
    description = models.TextField(blank=True, help_text="General description")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Auto-generate reference number if not provided."""
        if not self.reference_no:
            prefix = self._get_prefix()
            project_id = str(self.project.id).zfill(3)
            # Count existing objects of this type for this project to generate sequence
            # We use all_objects to include soft-deleted ones for unique sequence if needed,
            # but usually pk is enough. Here we use count for human-readable sequence.
            count = self.__class__.objects.filter(project=self.project).count() + 1
            self.reference_no = f"{prefix}-PRJ{project_id}-{str(count).zfill(3)}"
        super().save(*args, **kwargs)

    def _get_prefix(self):
        """Return prefix based on model class name."""
        mapping = {
            "LabourEntity": "LAB",
            "MaterialEntity": "MAT",
            "PlantEntity": "PLT",
            "SubcontractorEntity": "SUB",
            "OverheadEntity": "OVH",
        }
        return mapping.get(self.__class__.__name__, "ENT")

    def __str__(self):
        return f"{self.reference_no} - {self.name}"


class LabourEntity(BaseProjectEntity):
    """Labour entity definition."""

    person_name = models.CharField(max_length=255, help_text="Worker name")
    id_number = models.CharField(
        max_length=100, blank=True, help_text="ID/Passport number"
    )
    trade = models.CharField(max_length=100, blank=True, help_text="Trade/Specialty")
    skill_type = models.ForeignKey(
        "SiteManagement.SkillType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="labour_entities",
    )
    date_joined = models.DateField(
        null=True, blank=True, help_text="Date joined project"
    )

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.person_name
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Labour Entity"
        verbose_name_plural = "Labour Entities"
        ordering = ["name"]


class MaterialEntity(BaseProjectEntity):
    """Material entity definition."""

    supplier = models.CharField(
        max_length=255, blank=True, help_text="Preferred supplier"
    )
    items_received = models.TextField(blank=True, help_text="Detailed items/specs")
    invoice_number = models.CharField(max_length=100, blank=True)
    quantity = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Estimated quantity"
    )
    date_received = models.DateField(
        null=True, blank=True, help_text="Initial receipt date"
    )

    class Meta:
        verbose_name = "Material Entity"
        verbose_name_plural = "Material Entities"
        ordering = ["name"]


class PlantEntity(BaseProjectEntity):
    """Plant and Equipment entity definition."""

    class BreakdownStatus(models.TextChoices):
        OPERATIONAL = "OPERATIONAL", "Operational"
        BREAKDOWN = "BREAKDOWN", "Breakdown"
        UNDER_MAINTENANCE = "UNDER_MAINTENANCE", "Under Maintenance"
        RETIRED = "RETIRED", "Retired"

    plant_type = models.ForeignKey(
        "SiteManagement.PlantType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plant_entities",
    )
    specific_info = models.TextField(
        blank=True, help_text="Specific machine info (S/N, etc.)"
    )
    supplier = models.CharField(max_length=255, blank=True)
    breakdown_status = models.CharField(
        max_length=20,
        choices=BreakdownStatus.choices,
        default=BreakdownStatus.OPERATIONAL,
        help_text="Current breakdown status",
    )
    date = models.DateField(null=True, blank=True, help_text="Record date")

    def save(self, *args, **kwargs):
        if not self.name and self.plant_type:
            self.name = self.plant_type.name
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Plant Entity"
        verbose_name_plural = "Plant Entities"
        ordering = ["name"]


class SubcontractorEntity(BaseProjectEntity):
    """Subcontractor entity definition."""

    trade = models.CharField(max_length=100, blank=True)
    scope = models.TextField(blank=True, help_text="Scope of work")
    start_date = models.DateField(null=True, blank=True)
    planned_finish_date = models.DateField(null=True, blank=True)
    actual_finish_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Subcontractor Entity"
        verbose_name_plural = "Subcontractor Entities"
        ordering = ["name"]


class OverheadEntity(BaseProjectEntity):
    """Overhead entity definition."""

    category = models.CharField(
        max_length=100, blank=True, help_text="Overhead category"
    )

    class Meta:
        verbose_name = "Overhead Entity"
        verbose_name_plural = "Overhead Entities"
        ordering = ["name"]
