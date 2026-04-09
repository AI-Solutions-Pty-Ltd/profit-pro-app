"""Bi-Weekly Quality Report models (header + child tables)."""

from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class BiWeeklyQualityReport(BaseModel):
    """Header record for a bi-weekly quality inspection report."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="biweekly_quality_reports",
        help_text="Project this report belongs to",
    )
    period_start = models.DateField(help_text="Start of the two-week period")
    period_end = models.DateField(help_text="End of the two-week period")
    submitted_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="submitted_quality_reports",
        help_text="User who submitted this report",
    )
    notes = models.TextField(blank=True, help_text="Additional notes")

    class Meta:
        verbose_name = "Bi-Weekly Quality Report"
        verbose_name_plural = "Bi-Weekly Quality Reports"
        ordering = ["-period_end", "-created_at"]

    def __str__(self) -> str:
        return (
            f"Quality Report: {self.period_start} – {self.period_end} ({self.project})"
        )


class QualityActivityInspection(BaseModel):
    """Activity or work package inspected within a bi-weekly quality report."""

    class ApprovalStatus(models.TextChoices):
        APPROVED = "APPROVED", "Approved"
        CONDITIONAL = "CONDITIONAL", "Conditional Approval"
        REJECTED = "REJECTED", "Rejected"
        PENDING = "PENDING", "Pending"

    report = models.ForeignKey(
        BiWeeklyQualityReport,
        on_delete=models.CASCADE,
        related_name="activity_inspections",
        help_text="Parent quality report",
    )
    activity_or_work_package = models.CharField(
        max_length=255,
        help_text="Activity or work package that was inspected",
    )
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        help_text="Inspection approval status",
    )
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "Quality Activity Inspection"
        verbose_name_plural = "Quality Activity Inspections"

    def __str__(self) -> str:
        return f"{self.activity_or_work_package} – {self.get_approval_status_display()}"  # type: ignore


class QualityMaterialDelivery(BaseModel):
    """Material delivered on site during the reporting period."""

    report = models.ForeignKey(
        BiWeeklyQualityReport,
        on_delete=models.CASCADE,
        related_name="material_deliveries",
        help_text="Parent quality report",
    )
    date = models.DateField(help_text="Date of delivery")
    material = models.CharField(max_length=255, help_text="Material description")
    quantity = models.CharField(max_length=100, help_text="Quantity delivered")

    class Meta:
        verbose_name = "Quality Material Delivery"
        verbose_name_plural = "Quality Material Deliveries"
        ordering = ["date"]

    def __str__(self) -> str:
        return f"{self.material} x{self.quantity} ({self.date})"


class QualityWorkmanship(BaseModel):
    """Workmanship record for a specific activity."""

    report = models.ForeignKey(
        BiWeeklyQualityReport,
        on_delete=models.CASCADE,
        related_name="workmanship_records",
        help_text="Parent quality report",
    )
    activity = models.CharField(max_length=255, help_text="Activity checked")
    is_compliant = models.BooleanField(
        default=True,
        help_text="Compliant with drawings and specifications",
    )
    snag_defect = models.TextField(
        blank=True,
        help_text="Snag or defect identified (if non-compliant)",
    )
    snag_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date the snag/defect was identified",
    )

    class Meta:
        verbose_name = "Quality Workmanship Record"
        verbose_name_plural = "Quality Workmanship Records"

    def __str__(self) -> str:
        status = "Compliant" if self.is_compliant else "Non-compliant"
        return f"{self.activity} – {status}"


class QualitySiteAudit(BaseModel):
    """Site inspection or audit entry within a bi-weekly quality report."""

    report = models.ForeignKey(
        BiWeeklyQualityReport,
        on_delete=models.CASCADE,
        related_name="site_audits",
        help_text="Parent quality report",
    )
    date = models.DateField(help_text="Date of inspection/audit")
    inspector = models.CharField(
        max_length=255,
        help_text="Name of inspector or auditor",
    )
    audit_findings = models.TextField(
        help_text="Findings from the inspection or audit",
    )

    class Meta:
        verbose_name = "Quality Site Audit"
        verbose_name_plural = "Quality Site Audits"
        ordering = ["date"]

    def __str__(self) -> str:
        return f"Audit by {self.inspector} on {self.date}"
