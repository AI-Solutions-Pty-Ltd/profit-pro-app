from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse

from app.BillOfQuantities.models.forecast_models import Forecast
from app.BillOfQuantities.models.payment_certificate_models import PaymentCertificate
from app.BillOfQuantities.models.structure_models import LineItem
from app.core.Utilities.models import BaseModel, sum_queryset
from app.Project.models.category_models import ProjectCategory
from app.Project.models.client_models import Client

if TYPE_CHECKING:
    from app.Account.models import Account

    from .planned_value_models import PlannedValue
    from .project_roles import ProjectRole
    from .signatories_models import Signatories


def get_months_between(start_date: date, end_date: date) -> list[date]:
    """Generate a list of month start dates between start_date and end_date."""
    months = []
    current = start_date.replace(day=1)
    end = end_date.replace(day=1)

    while current <= end:
        months.append(current)
        current += relativedelta(months=1)

    return months


class Project(BaseModel):
    class Status(models.TextChoices):
        SETUP = "SETUP", "Setup"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        FINAL_ACCOUNT_ISSUED = "FINAL_ACCOUNT_ISSUED", "Final Account Issued"

    portfolio = models.ForeignKey(
        "Project.Portfolio",
        on_delete=models.SET_NULL,
        null=True,
        related_name="projects",
    )
    users = models.ManyToManyField(
        "Account.Account",
        related_name="projects",
        help_text="Users who have access to this project",
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=255, choices=Status.choices, default=Status.SETUP
    )
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    contract_number = models.CharField(max_length=255, blank=True)
    contract_clause = models.CharField(max_length=255, blank=True)
    vat = models.BooleanField(default=False)

    # Contractual dates for contract management
    contractual_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Contractual/possession start date",
    )
    contractual_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Original contractual completion date",
    )
    revised_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Current revised completion date (after extensions)",
    )
    practical_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of practical completion",
    )
    defects_liability_period = models.IntegerField(
        null=True,
        blank=True,
        help_text="Defects liability period in months",
    )
    final_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Final completion date (end of defects liability)",
    )

    # Contract duration
    contract_duration_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Original contract duration in calendar days",
    )
    approved_extension_days = models.IntegerField(
        default=0,
        help_text="Total approved extension of time in days",
    )

    # Retention settings
    retention_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Retention percentage (e.g., 10.00 for 10%)",
    )
    retention_limit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Retention limit as percentage of contract value",
    )
    retention_release_practical = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage of retention released at practical completion",
    )

    # Advance payment settings
    advance_payment_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Advance payment percentage",
    )
    advance_recovery_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Advance recovery percentage per certificate",
    )
    final_payment_certificate = models.ForeignKey(
        "BillOfQuantities.PaymentCertificate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="final_account_project",
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        help_text="Project category (e.g., Education, Health, Roads)",
    )

    # Project team roles - all as ManyToMany for multiple users per role
    contractors = models.ManyToManyField(
        "Account.Account",
        blank=True,
        related_name="contractor_projects",
        help_text="Contractors responsible for the project",
    )
    quantity_surveyors = models.ManyToManyField(
        "Account.Account",
        blank=True,
        related_name="qs_projects",
        help_text="Quantity Surveyors for the project",
    )
    lead_consultants = models.ManyToManyField(
        "Account.Account",
        blank=True,
        related_name="lead_consultant_projects",
        help_text="Lead Consultants (e.g., Principal Agents)",
    )
    client_representatives = models.ManyToManyField(
        "Account.Account",
        blank=True,
        related_name="client_rep_projects",
        help_text="Client Representatives",
    )

    if TYPE_CHECKING:
        payment_certificates: QuerySet[PaymentCertificate]
        line_items: QuerySet[LineItem]
        forecasts: QuerySet[Forecast]
        signatories: QuerySet["Signatories"]
        planned_values: QuerySet["PlannedValue"]
        users: models.ManyToManyField["Account", "Account"]
        project_roles: QuerySet["ProjectRole"]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-name"]

    def save(self, *args, **kwargs) -> None:
        """Override save to manage PlannedValue instances when dates change."""
        # Import here to avoid circular import
        from app.Project.models.planned_value_models import PlannedValue

        # Check if this is an existing instance
        dates_changed = False
        old_start_date = None
        old_end_date = None

        if self.pk:
            try:
                old_instance = Project.objects.get(pk=self.pk)
                old_start_date = old_instance.start_date
                old_end_date = old_instance.end_date
                dates_changed = (
                    old_start_date != self.start_date or old_end_date != self.end_date
                )
            except Project.DoesNotExist:
                pass

        # Save the project first
        super().save(*args, **kwargs)

        # Only manage PlannedValue instances if dates changed and we have valid dates
        if dates_changed and self.start_date and self.end_date:
            self._sync_planned_values(PlannedValue)

    def _sync_planned_values(self, planned_value_model) -> None:
        """Sync PlannedValue instances with the project's date range.

        - Soft delete instances outside the new date range
        - Restore soft-deleted instances inside the range or create new ones
        """
        # Get the valid months for the new date range
        valid_months = set(get_months_between(self.start_date, self.end_date))

        # Get all PlannedValue instances (including soft-deleted) for this project
        all_planned_values = planned_value_model.all_objects.filter(project=self)

        for pv in all_planned_values:
            period_normalized = pv.period.replace(day=1)
            if period_normalized in valid_months:
                # Period is within range - restore if soft-deleted
                if pv.is_deleted:
                    pv.restore()
            else:
                # Period is outside range - soft delete if not already deleted
                if not pv.is_deleted:
                    pv.soft_delete()

        # Create new PlannedValue instances for months that don't exist yet
        existing_periods = {
            pv.period.replace(day=1)
            for pv in planned_value_model.all_objects.filter(project=self)
        }

        for month in valid_months:
            if month not in existing_periods:
                planned_value_model.objects.create(
                    project=self,
                    period=month,
                    value=Decimal("0.00"),
                    forecast_value=None,
                    work_completed_percent=None,
                )

    ##################
    # URLS
    ##################

    def get_absolute_url(self):
        return reverse("project:project-management", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse("project:portfolio-dashboard")

    @staticmethod
    def get_create_url():
        return reverse("project:project-create")

    def get_update_url(self):
        return reverse("project:project-update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse("project:project-delete", kwargs={"pk": self.pk})

    def get_structure_upload_url(self):
        return reverse(
            "bill_of_quantities:structure-upload", kwargs={"project_pk": self.pk}
        )

    @property
    def setup(self: "Project") -> bool:
        """Is project fully setup or not"""
        if not self.start_date:
            return False
        if not self.end_date:
            return False
        if not self.line_items:
            return False
        if not self.planned_values:
            return False
        return True

    @property
    def original_contract_value(self: "Project") -> Decimal:
        all_line_items = self.line_items.all()
        original_line_items = all_line_items.filter(addendum=False, special_item=False)
        return sum_queryset(original_line_items, "total_price")

    @property
    def addendum_contract_value(self: "Project") -> Decimal:
        """This together with original_contract_value makes up the total revised contract value"""
        all_line_items = self.line_items.all()
        addendum_line_items = all_line_items.filter(addendum=True)
        return sum_queryset(addendum_line_items, "total_price")

    @property
    def revised_contract_value(self: "Project") -> Decimal:
        """This together with original_contract_value makes up the total revised contract value"""
        return self.original_contract_value + self.addendum_contract_value

    @property
    def special_contract_value(self: "Project") -> Decimal:
        """Not Part of budget, but still has value"""
        all_line_items = self.line_items.all()
        special_line_items = all_line_items.filter(special_item=True)
        return sum_queryset(special_line_items, "total_price")

    @property
    def contract_addendum_value(self: "Project") -> Decimal:
        return self.addendum_contract_value + self.special_contract_value

    @property
    def total_contract_value(self: "Project") -> Decimal:
        return sum_queryset(self.line_items.all(), "total_price")

    ##################
    # Payment Certificates
    ##################

    @property
    def active_payment_certificate(self: "Project") -> Optional["PaymentCertificate"]:
        """Get the most recent active payment certificate (DRAFT, SUBMITTED, or REJECTED)."""

        return (
            self.payment_certificates.filter(
                status__in=[
                    PaymentCertificate.Status.DRAFT,
                    PaymentCertificate.Status.SUBMITTED,
                    PaymentCertificate.Status.REJECTED,
                ]
            )
            .order_by("-created_at")
            .first()
        )

    @property
    def get_line_items(self: "Project"):
        return self.line_items.select_related(
            "structure", "bill", "package"
        ).prefetch_related("actual_transactions")

    @property
    def get_special_line_items(self: "Project"):
        return (
            self.line_items.filter(special_item=True)
            .select_related("structure", "bill", "package")
            .prefetch_related("actual_transactions")
        )

    @property
    def total_certified_to_date(self: "Project") -> Decimal:
        return sum_queryset(
            self.payment_certificates.filter(status=PaymentCertificate.Status.APPROVED),
            "actual_transactions__total_price",
        )

    @property
    def total_certified_to_date_percentage(self: "Project") -> Decimal:
        if not self.total_certified_to_date:
            return Decimal(0)
        return Decimal(
            round(self.total_contract_value / self.total_certified_to_date * 100, 2)
        )

    @property
    def project_manager(self: "Project") -> Optional["Account"]:
        """Get the first lead consultant as the project manager."""
        return self.lead_consultants.first()

    ##################
    # Forecasts
    ##################
    @property
    def latest_forecast(self: "Project") -> Forecast | None:
        return self.forecasts.filter(status=Forecast.Status.APPROVED).first()

    @property
    def forecast_variance_percent(self: "Project") -> Decimal | None:
        revised_contract_value = self.total_contract_value
        latest_forecast = self.latest_forecast
        if not revised_contract_value or not latest_forecast:
            return None
        return Decimal(
            round(
                (latest_forecast.total_forecast - revised_contract_value)
                / revised_contract_value,
                2,
            )
        )

    ##################
    # Final Reports
    ##################

    # planned_value
    def get_planned_value(self: "Project", date: datetime | None = None) -> Decimal:
        """From Cashflow Forecast included as part of the baseline/Contract WBS"""
        if not date:
            date = datetime.now()
        planned_values = self.planned_values.filter(
            period__lte=date,
        )
        return sum_queryset(planned_values, "value")

    @property
    def planned_value(self: "Project") -> Decimal:
        return self.get_planned_value()

    # actual_cost
    def get_actual_cost(self: "Project", date: datetime | None = None) -> Decimal:
        """Total certified amount from approved payment certificates for the given month."""
        if not date:
            date = datetime.now()
        approved_certificates = self.payment_certificates.filter(
            approved_on__lte=date,
            status=PaymentCertificate.Status.APPROVED,
        )
        return sum_queryset(approved_certificates, "actual_transactions__total_price")

    @property
    def actual_cost(self: "Project") -> Decimal:
        return self.get_actual_cost()

    # actual_cost_percentage
    def get_actual_cost_percentage(
        self: "Project", date: datetime | None = None
    ) -> Decimal:
        """Percentage of the total contract value that has been certified

        Formula: (AC / TCV) * 100
        """
        if not date:
            date = datetime.now()

        if not self.total_contract_value:
            return Decimal(0)
        return round(self.get_actual_cost(date) / self.total_contract_value * 100, 2)

    @property
    def actual_cost_percentage(self: "Project") -> Decimal:
        return self.get_actual_cost_percentage()

    # forecast_cost
    def get_forecast_cost(self: "Project", date: datetime | None = None) -> Decimal:
        """From Forecast to Completion Cost in the Cost Report"""
        if not date:
            date = datetime.now()
        forecast = self.forecasts.filter(
            period__lte=date,
            status=Forecast.Status.APPROVED,
        ).first()
        return forecast.total_forecast if forecast else Decimal("0")

    @property
    def forecast_cost(self: "Project") -> Decimal:
        return self.get_forecast_cost()

    # earned_value
    def get_earned_value(
        self: "Project", date: datetime | None = None
    ) -> Decimal | None:
        """Earned Value
        Formula:
            Original Budget * Actual Cost Percentage"""
        if not date:
            date = datetime.now()
        original_contract_value = self.original_contract_value
        actual_cost_percentage = self.get_actual_cost_percentage(date)
        if not original_contract_value or not actual_cost_percentage:
            return None
        return original_contract_value * (actual_cost_percentage / 100)

    @property
    def earned_value(self: "Project") -> Decimal | None:
        return self.get_earned_value()

    # cost_variance
    def get_cost_variance(self: "Project", date: datetime | None = None) -> Decimal:
        """Earned Value - Actual Cost"""
        if not date:
            date = datetime.now()
        return (self.get_earned_value(date) or Decimal("0.00")) - self.get_actual_cost(
            date
        )

    @property
    def cost_variance(self: "Project") -> Decimal:
        return self.get_cost_variance()

    # schedule_variance
    def get_schedule_variance(self: "Project", date: datetime | None = None) -> Decimal:
        if not date:
            date = datetime.now()
        return (
            self.get_earned_value(date) or Decimal("0.00")
        ) - self.get_planned_value(date)

    @property
    def schedule_variance(self: "Project") -> Decimal:
        return self.get_schedule_variance()

    # cost_performance_index
    def get_cost_performance_index(
        self: "Project", date: datetime | None = None
    ) -> Decimal | None:
        """Earned Value/Actual Cost
        CPI Interpretations:
            CPI < 1 Means the project has overrun the budget
            CPI = 0 Means the project is on Budget
            CPI > 1 Means the Project is under Budget
        """
        if not date:
            date = datetime.now()
        earned = self.get_earned_value(date)
        actual = self.get_actual_cost(date)
        if not earned or not actual or actual == 0:
            return None
        return round(earned / actual, 2)

    # schedule_performance_index
    def get_schedule_performance_index(
        self: "Project", date: datetime | None = None
    ) -> Decimal | None:
        """Earned Value/Planned Value
        SPI Interpretations:
            SPI < 1 Means the project is behind schedule
            SPI = 0 Means the project is on Schedule
            SPI > 1 Means the Project is ahead of Schedule
        """
        if not date:
            date = datetime.now()
        earned = self.get_earned_value(date)
        planned = self.get_planned_value(date)
        if not earned or not planned or planned == 0:
            return None
        return round(earned / planned, 2)

    @property
    def schedule_performance_index(self: "Project") -> Decimal | None:
        return self.get_schedule_performance_index()

    # estimate_at_completion
    def get_estimate_at_completion(
        self: "Project", date: datetime | None = None
    ) -> Decimal | None:
        """Estimate at Completion (EAC): Original budget / cpi"""
        if not date:
            date = datetime.now()

        original_budget = self.total_contract_value
        cpi = self.get_cost_performance_index(date)
        if not cpi or cpi == 0:
            return None
        return original_budget / cpi

    @property
    def estimate_at_completion(self: "Project") -> Decimal | None:
        return self.get_estimate_at_completion()

    # estimate_to_complete
    def get_estimate_to_complete(
        self: "Project", date: datetime | None = None
    ) -> Decimal | None:
        """Estimate to Complete (ETC):

        Formula:
            EAC - AC"""
        if not date:
            date = datetime.now()

        eac = self.get_estimate_at_completion(date)
        ac = self.get_actual_cost(date)
        if not eac or not ac:
            return None
        return eac - ac

    @property
    def estimate_to_complete(self: "Project") -> Decimal | None:
        return self.get_estimate_to_complete()

    # to_complete_project_index
    def get_to_complete_project_index(
        self: "Project", date: datetime | None = None
    ) -> Decimal | None:
        """To Complete Project Index (TCPI):

        Formula:
            (Total Revised Budget - Actual Cost) / (Estimate To Complete - Actual Cost)
        """
        if not date:
            date = datetime.now()

        total_revised_budget = self.total_contract_value
        actual_cost = self.get_actual_cost(date)
        eac = self.get_estimate_at_completion(date)
        if not total_revised_budget or not actual_cost or not eac:
            return None
        return round((total_revised_budget - actual_cost) / (eac - actual_cost), 2)

    @property
    def to_complete_project_index(self: "Project") -> Decimal | None:
        return self.get_to_complete_project_index()
