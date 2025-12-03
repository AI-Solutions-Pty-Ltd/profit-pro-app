"""
Cashflow Management Models.

Provides models for:
- Baseline Cashflow (original planned values)
- Revised Baseline (adjusted baseline with date extensions)
- Cashflow Forecast (forward-looking projections)
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet

from app.Account.models import Account
from app.core.Utilities.models import BaseModel

if TYPE_CHECKING:
    from app.Project.models import Project


class BaselineCashflow(BaseModel):
    """
    Baseline Cashflow - the original planned values for the project.

    This represents the initial cash flow projection based on the
    original contract program and value.
    """

    class Status(models.TextChoices):
        """Status of baseline."""

        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        SUPERSEDED = "SUPERSEDED", "Superseded"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="baseline_cashflows",
        help_text="Project this cashflow belongs to",
    )
    version = models.IntegerField(
        default=1,
        help_text="Version number of this baseline",
    )
    period = models.DateField(
        help_text="Period (month) for this cashflow value",
    )
    planned_value: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        help_text="Planned value for this period",
    )
    cumulative_value: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cumulative planned value up to this period",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    notes = models.TextField(
        blank=True,
        default="",
    )
    approved_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_baseline_cashflows",
    )
    approved_on = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Baseline Cashflow"
        verbose_name_plural = "Baseline Cashflows"
        ordering = ["period"]
        unique_together = [["project", "version", "period"]]
        indexes = [
            models.Index(fields=["project", "version"]),
            models.Index(fields=["period"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.name} v{self.version} - {self.period}"

    def clean(self) -> None:
        """Normalize period to first day of month."""
        if self.period:
            self.period = self.period.replace(day=1)

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_current_baseline(cls, project: "Project") -> QuerySet["BaselineCashflow"]:
        """Get the current (latest approved) baseline for a project."""
        latest_version = (
            cls.objects.filter(project=project, status=cls.Status.APPROVED)
            .order_by("-version")
            .values_list("version", flat=True)
            .first()
        )
        if latest_version:
            return cls.objects.filter(
                project=project, version=latest_version, status=cls.Status.APPROVED
            )
        return cls.objects.none()


class RevisedBaseline(BaseModel):
    """
    Revised Baseline - adjusted baseline with capability to extend project dates.

    This allows for re-baselining the project when significant changes occur,
    such as approved variations that extend the completion date.
    """

    class Status(models.TextChoices):
        """Status of revised baseline."""

        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted for Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class RevisionReason(models.TextChoices):
        """Reason for revision."""

        VARIATION = "VARIATION", "Contract Variation"
        EXTENSION = "EXTENSION", "Time Extension"
        ACCELERATION = "ACCELERATION", "Acceleration"
        RE_SEQUENCE = "RE_SEQUENCE", "Re-sequencing of Works"
        OTHER = "OTHER", "Other"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="revised_baselines",
        help_text="Project this revised baseline belongs to",
    )
    revision_number = models.IntegerField(
        default=1,
        help_text="Revision number",
    )
    revision_date = models.DateField(
        help_text="Date of this revision",
    )
    revision_reason = models.CharField(
        max_length=30,
        choices=RevisionReason.choices,
        default=RevisionReason.OTHER,
        help_text="Reason for revising the baseline",
    )
    reason_description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of revision reason",
    )

    # Original dates (before revision)
    original_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Original project start date",
    )
    original_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Original project completion date",
    )

    # Revised dates (after revision)
    revised_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Revised project start date",
    )
    revised_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Revised project completion date",
    )

    # Value changes
    original_contract_value: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original contract value before revision",
    )
    revised_contract_value: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Revised contract value after this revision",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    notes = models.TextField(
        blank=True,
        default="",
    )

    # Approval tracking
    submitted_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_revised_baselines",
    )
    submitted_on = models.DateTimeField(
        null=True,
        blank=True,
    )
    approved_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_revised_baselines",
    )
    approved_on = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Link to variation that caused this revision
    linked_variation = models.ForeignKey(
        "BillOfQuantities.ContractVariation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revised_baselines",
        help_text="Variation that triggered this baseline revision",
    )

    class Meta:
        verbose_name = "Revised Baseline"
        verbose_name_plural = "Revised Baselines"
        ordering = ["-revision_date", "-revision_number"]
        unique_together = [["project", "revision_number"]]
        indexes = [
            models.Index(fields=["project", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.name} - Revision {self.revision_number}"

    @property
    def time_extension_days(self) -> int | None:
        """Calculate days extension from this revision."""
        if self.original_completion_date and self.revised_completion_date:
            delta = self.revised_completion_date - self.original_completion_date
            return delta.days
        return None

    @property
    def value_change(self) -> Decimal | None:
        """Calculate value change from this revision."""
        if self.original_contract_value and self.revised_contract_value:
            return self.revised_contract_value - self.original_contract_value
        return None


class RevisedBaselineDetail(BaseModel):
    """
    Period-by-period detail for a revised baseline.

    Each revision can have detailed monthly cashflow projections.
    """

    revised_baseline = models.ForeignKey(
        RevisedBaseline,
        on_delete=models.CASCADE,
        related_name="details",
        help_text="Parent revised baseline",
    )
    period = models.DateField(
        help_text="Period (month) for this value",
    )
    planned_value: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        help_text="Planned value for this period",
    )
    cumulative_value: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cumulative planned value up to this period",
    )
    notes = models.TextField(
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = "Revised Baseline Detail"
        verbose_name_plural = "Revised Baseline Details"
        ordering = ["period"]
        unique_together = [["revised_baseline", "period"]]

    def __str__(self) -> str:
        return f"{self.revised_baseline} - {self.period}"

    def clean(self) -> None:
        """Normalize period to first day of month."""
        if self.period:
            self.period = self.period.replace(day=1)

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)


class CashflowForecast(BaseModel):
    """
    Cashflow Forecast - forward-looking projections.

    Used for projecting expected cash flows based on current progress
    and anticipated completion. Can extend beyond original completion date.
    """

    class Status(models.TextChoices):
        """Status of forecast."""

        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="cashflow_forecasts",
        help_text="Project this forecast belongs to",
    )
    forecast_date = models.DateField(
        help_text="Date when this forecast was created",
    )
    forecast_period = models.DateField(
        help_text="Period (month) being forecast",
    )

    # Forecast values
    forecast_value: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        help_text="Forecasted value for this period",
    )
    cumulative_forecast: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cumulative forecast up to this period",
    )

    # Comparison to baseline
    baseline_value: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original baseline value for comparison",
    )
    variance: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Variance from baseline (forecast - baseline)",
    )

    # Forecast completion date
    forecast_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Forecasted project completion date",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    notes = models.TextField(
        blank=True,
        default="",
    )
    captured_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="captured_cashflow_forecasts",
    )
    approved_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_cashflow_forecasts",
    )

    class Meta:
        verbose_name = "Cashflow Forecast"
        verbose_name_plural = "Cashflow Forecasts"
        ordering = ["forecast_period"]
        indexes = [
            models.Index(fields=["project", "forecast_date"]),
            models.Index(fields=["forecast_period"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.name} - Forecast {self.forecast_period}"

    def clean(self) -> None:
        """Normalize period to first day of month."""
        if self.forecast_period:
            self.forecast_period = self.forecast_period.replace(day=1)

    def save(self, *args, **kwargs) -> None:
        self.clean()
        # Calculate variance if both values present
        if self.forecast_value and self.baseline_value:
            self.variance = self.forecast_value - self.baseline_value
        super().save(*args, **kwargs)

    @classmethod
    def get_latest_forecast(cls, project: "Project") -> QuerySet["CashflowForecast"]:
        """Get the latest forecast for a project."""
        latest_date = (
            cls.objects.filter(project=project)
            .order_by("-forecast_date")
            .values_list("forecast_date", flat=True)
            .first()
        )
        if latest_date:
            return cls.objects.filter(project=project, forecast_date=latest_date)
        return cls.objects.none()
