"""Quality Control Register model for tracking QC inspections."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class QualityControl(BaseModel):
    """Track quality control inspections and results."""

    class Result(models.TextChoices):
        PASS = "PASS", "Pass"
        FAIL = "FAIL", "Fail"
        CONDITIONAL = "CONDITIONAL", "Conditional Pass"
        PENDING = "PENDING", "Pending"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="quality_controls",
        help_text="Project this QC record belongs to",
    )
    date = models.DateField(help_text="Date of inspection")
    qc_item = models.CharField(max_length=255, help_text="Quality control item")
    area_location = models.CharField(max_length=255, help_text="Area/Location")
    inspector = models.CharField(max_length=255, help_text="Inspector name")
    result = models.CharField(
        max_length=20,
        choices=Result.choices,
        default=Result.PENDING,
        help_text="Inspection result",
    )
    rectification_needed = models.TextField(
        blank=True, help_text="Rectification work needed"
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.qc_item} - {self.area_location} - {self.date}"

    class Meta:
        verbose_name = "Quality Control"
        verbose_name_plural = "Quality Control Records"
        ordering = ["-date", "-created_at"]
