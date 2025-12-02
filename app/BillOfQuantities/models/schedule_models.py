"""
Schedule Forecast Models.

Provides models for:
- Schedule Forecast (planned vs forecast completion dates)
- Sectional Completion Dates (for contracts with multiple sections)
"""

from datetime import date
from decimal import Decimal

from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class SectionalCompletionDate(BaseModel):
    """
    Sectional Completion Dates for contracts with multiple sections.

    Some contracts have multiple sections that must be completed by
    different dates. This tracks both planned and actual/forecast dates.
    """

    class Status(models.TextChoices):
        """Status of the section."""

        NOT_STARTED = "NOT_STARTED", "Not Started"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        DELAYED = "DELAYED", "Delayed"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="sectional_completion_dates",
        help_text="Project this section belongs to",
    )
    section_name = models.CharField(
        max_length=255,
        help_text="Name or identifier of the section",
    )
    section_description = models.TextField(
        blank=True,
        default="",
        help_text="Description of what this section covers",
    )
    section_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Contract clause/reference for this section",
    )

    # Planned dates
    planned_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Planned start date for this section",
    )
    planned_completion_date = models.DateField(
        help_text="Contractual/planned completion date for this section",
    )

    # Forecast/Actual dates
    forecast_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Forecast/actual start date",
    )
    forecast_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Forecast completion date",
    )
    actual_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual completion date (when completed)",
    )

    # Status and value
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    section_value: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Value of work in this section",
    )
    percentage_complete: Decimal = models.DecimalField(  # type: ignore
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage complete (0-100)",
    )

    # Penalty/Bonus tracking
    has_penalty = models.BooleanField(
        default=False,
        help_text="Whether penalties apply for late completion",
    )
    penalty_rate: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Penalty rate per day/week",
    )
    penalty_period = models.CharField(
        max_length=20,
        blank=True,
        default="DAY",
        help_text="Period for penalty calculation (DAY, WEEK, MONTH)",
    )
    penalty_cap: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum penalty amount",
    )

    notes = models.TextField(
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = "Sectional Completion Date"
        verbose_name_plural = "Sectional Completion Dates"
        ordering = ["planned_completion_date"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["planned_completion_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.name} - {self.section_name}"

    @property
    def days_variance(self) -> int | None:
        """Calculate days variance between planned and forecast."""
        if self.planned_completion_date and self.forecast_completion_date:
            delta = self.forecast_completion_date - self.planned_completion_date
            return delta.days
        return None

    @property
    def is_delayed(self) -> bool:
        """Check if section is delayed."""
        variance = self.days_variance
        if variance is not None:
            return variance > 0
        return False

    @property
    def days_to_completion(self) -> int | None:
        """Calculate days remaining to planned completion."""
        if self.planned_completion_date:
            delta = self.planned_completion_date - date.today()
            return delta.days
        return None

    @property
    def estimated_penalty(self) -> Decimal | None:
        """Calculate estimated penalty based on delay."""
        variance = self.days_variance
        if variance and variance > 0 and self.penalty_rate:
            penalty = self.penalty_rate * Decimal(variance)
            if self.penalty_cap:
                return min(penalty, self.penalty_cap)
            return penalty
        return None


class ScheduleForecast(BaseModel):
    """
    Schedule Forecast - tracks planned vs forecast completion.

    Provides a snapshot view of project schedule status including
    overall project and sectional completion forecasts.
    """

    class Status(models.TextChoices):
        """Status of forecast."""

        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="schedule_forecasts",
        help_text="Project this forecast belongs to",
    )
    forecast_date = models.DateField(
        help_text="Date when this forecast was created",
    )
    reporting_period = models.DateField(
        help_text="Reporting period (month) for this forecast",
    )

    # Overall project dates
    planned_project_completion = models.DateField(
        help_text="Current contractual/planned completion date",
    )
    forecast_project_completion = models.DateField(
        help_text="Forecast completion date based on current progress",
    )

    # Progress indicators
    overall_percentage_complete: Decimal = models.DecimalField(  # type: ignore
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Overall project percentage complete",
    )
    planned_percentage_complete: Decimal = models.DecimalField(  # type: ignore
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Planned percentage complete for this date",
    )

    # Time analysis
    original_duration_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Original project duration in days",
    )
    elapsed_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Days elapsed since project start",
    )
    remaining_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Remaining days to forecast completion",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Analysis notes and observations",
    )
    captured_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="captured_schedule_forecasts",
    )
    approved_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_schedule_forecasts",
    )

    class Meta:
        verbose_name = "Schedule Forecast"
        verbose_name_plural = "Schedule Forecasts"
        ordering = ["-forecast_date", "-reporting_period"]
        indexes = [
            models.Index(fields=["project", "forecast_date"]),
            models.Index(fields=["reporting_period"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.name} - {self.reporting_period}"

    def clean(self) -> None:
        """Normalize period to first day of month."""
        if self.reporting_period:
            self.reporting_period = self.reporting_period.replace(day=1)

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)

    @property
    def days_variance(self) -> int | None:
        """Calculate days variance between planned and forecast."""
        if self.planned_project_completion and self.forecast_project_completion:
            delta = self.forecast_project_completion - self.planned_project_completion
            return delta.days
        return None

    @property
    def schedule_variance_percentage(self) -> Decimal | None:
        """Calculate schedule variance as percentage."""
        if self.overall_percentage_complete and self.planned_percentage_complete:
            return self.overall_percentage_complete - self.planned_percentage_complete
        return None

    @property
    def is_delayed(self) -> bool:
        """Check if project is delayed."""
        variance = self.days_variance
        if variance is not None:
            return variance > 0
        return False

    @classmethod
    def get_latest_forecast(cls, project: Project) -> "ScheduleForecast | None":
        """Get the latest forecast for a project."""
        return cls.objects.filter(project=project).order_by("-forecast_date").first()


class ScheduleForecastSection(BaseModel):
    """
    Section-level detail for a Schedule Forecast.

    Links forecast to sectional completion dates with forecast values.
    """

    schedule_forecast = models.ForeignKey(
        ScheduleForecast,
        on_delete=models.CASCADE,
        related_name="section_forecasts",
        help_text="Parent schedule forecast",
    )
    sectional_completion = models.ForeignKey(
        SectionalCompletionDate,
        on_delete=models.CASCADE,
        related_name="forecast_entries",
        help_text="Sectional completion date being forecast",
    )

    # Forecast values at time of forecast
    forecast_completion_date = models.DateField(
        help_text="Forecast completion date for this section",
    )
    percentage_complete: Decimal = models.DecimalField(  # type: ignore
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage complete at forecast date",
    )
    notes = models.TextField(
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = "Schedule Forecast Section"
        verbose_name_plural = "Schedule Forecast Sections"
        ordering = ["sectional_completion__planned_completion_date"]

    def __str__(self) -> str:
        return f"{self.schedule_forecast} - {self.sectional_completion.section_name}"

    @property
    def days_variance(self) -> int | None:
        """Calculate days variance for this section."""
        if (
            self.sectional_completion.planned_completion_date
            and self.forecast_completion_date
        ):
            delta = (
                self.forecast_completion_date
                - self.sectional_completion.planned_completion_date
            )
            return delta.days
        return None
