from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from django.db import models
from django.db.models import QuerySet
from django.urls import reverse

from app.Account.models import Account
from app.BillOfQuantities.models.forecast_models import Forecast
from app.BillOfQuantities.models.payment_certificate_models import PaymentCertificate
from app.BillOfQuantities.models.structure_models import LineItem
from app.core.Utilities.models import BaseModel, sum_queryset

if TYPE_CHECKING:
    from .planned_value_models import PlannedValue
    from .signatories_models import Signatories


class Client(BaseModel):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="client"
    )
    consultant = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultant",
    )
    description = models.TextField()
    if TYPE_CHECKING:
        projects: QuerySet["Project"]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["-created_at"]


class Portfolio(BaseModel):
    users = models.ManyToManyField(Account, null=True, related_name="portfolios")

    def __str__(self) -> str:
        return super().__str__()

    if TYPE_CHECKING:
        projects: QuerySet["Project"]

    @property
    def active_projects(self) -> QuerySet["Project"]:
        return self.projects.filter(
            status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED]
        )

    @property
    def total_contract_value(self) -> Decimal:
        return sum_queryset(self.active_projects, "line_items__total_price")

    @property
    def total_forecast_value(self) -> Decimal:
        total_forecast_value = Decimal(0)
        for project in self.active_projects:
            last_forecast: Forecast | None = project.forecasts.order_by(
                "-period"
            ).last()
            if last_forecast:
                total_forecast_value += last_forecast.total_forecast
        return total_forecast_value

    @property
    def total_certified_value(self) -> Decimal:
        return sum_queryset(
            self.active_projects,
            "payment_certificates__actual_transactions__total_price",
        )

    def cost_performance_index(
        self: "Portfolio", date: datetime | None
    ) -> Decimal | None:
        """Portfolio-level CPI (average of all active projects)."""
        if not date:
            date = datetime.now()
        active_count = self.active_projects.count()
        if active_count == 0:
            return None
        cpi = Decimal(0)
        valid_projects = 0
        for project in self.active_projects:
            try:
                project_cpi = project.cost_performance_index(date)
                if project_cpi:
                    cpi += project_cpi
                    valid_projects += 1
            except (ZeroDivisionError, TypeError):
                print(f"Error calculating CPI for project {project.name}")
                continue
        if valid_projects == 0:
            return None
        return round(cpi / Decimal(valid_projects), 2)

    def schedule_performance_index(
        self: "Portfolio", date: datetime | None
    ) -> Decimal | None:
        """Portfolio-level SPI (average of all active projects)."""
        if not date:
            date = datetime.now()
        active_count = self.active_projects.count()
        if active_count == 0:
            return None
        spi = Decimal(0)
        valid_projects = 0
        for project in self.active_projects:
            try:
                project_spi = project.schedule_performance_index(date)
                if project_spi:
                    spi += project_spi
                    valid_projects += 1
            except (ZeroDivisionError, TypeError):
                continue
        if valid_projects == 0:
            return None
        return round(spi / Decimal(valid_projects), 2)


class Project(BaseModel):
    class Status(models.TextChoices):
        SETUP = "SETUP", "Setup"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        FINAL_ACCOUNT_ISSUED = "FINAL_ACCOUNT_ISSUED", "Final Account Issued"

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.SET_NULL, null=True, related_name="projects"
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="projects"
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

    # Project team roles
    contractor = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_projects",
        help_text="Contractor responsible for the project",
    )
    quantity_surveyor = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="qs_projects",
        help_text="Quantity Surveyor for the project",
    )
    lead_consultant = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_consultant_projects",
        help_text="Lead Consultant (e.g., Principal Agent)",
    )
    client_representative = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_rep_projects",
        help_text="Client Representative",
    )

    if TYPE_CHECKING:
        payment_certificates: QuerySet[PaymentCertificate]
        line_items: QuerySet[LineItem]
        forecasts: QuerySet[Forecast]
        signatories: QuerySet["Signatories"]
        planned_values: QuerySet["PlannedValue"]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-name"]

    def get_absolute_url(self):
        return reverse("project:project-management", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse("project:portfolio-list")

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
    def setup(self) -> bool:
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
    def get_original_contract_value(self) -> Decimal:
        all_line_items = self.line_items.all()
        original_line_items = all_line_items.filter(addendum=False, special_item=False)
        return sum_queryset(original_line_items, "total_price")

    @property
    def get_addendum_contract_value(self) -> Decimal:
        all_line_items = self.line_items.all()
        addendum_line_items = all_line_items.filter(addendum=True)
        return sum_queryset(addendum_line_items, "total_price")

    @property
    def contract_addendum_value(self) -> Decimal:
        return self.get_addendum_contract_value + self.get_special_contract_value

    @property
    def get_special_contract_value(self) -> Decimal:
        all_line_items = self.line_items.all()
        special_line_items = all_line_items.filter(special_item=True)
        return sum_queryset(special_line_items, "total_price")

    @property
    def get_total_contract_value(self) -> Decimal:
        return sum_queryset(self.line_items.all(), "total_price")

    @property
    def get_active_payment_certificate(self) -> Optional["PaymentCertificate"]:
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
    def get_line_items(self):
        return self.line_items.select_related(
            "structure", "bill", "package"
        ).prefetch_related("actual_transactions")

    @property
    def get_special_line_items(self):
        return (
            self.line_items.filter(special_item=True)
            .select_related("structure", "bill", "package")
            .prefetch_related("actual_transactions")
        )

    ##################
    # Final Reports
    ##################

    def planned_value(self, date: datetime | None = None) -> Decimal:
        """From Cashflow Forecast included as part of the baseline/Contract WBS"""
        if not date:
            date = datetime.now()
        planned_values = self.planned_values.filter(
            period__month=date.month,
            period__year=date.year,
        )
        return sum_queryset(planned_values, "value")

    def actual_cost(self, date: datetime | None = None) -> Decimal:
        """Total certified amount from approved payment certificates for the given month."""
        if not date:
            date = datetime.now()
        payment_certificates = self.payment_certificates.filter(
            approved_on__month=date.month,
            approved_on__year=date.year,
            status=PaymentCertificate.Status.APPROVED,
        )
        return sum_queryset(payment_certificates, "actual_transactions__total_price")

    def forecast_cost(self, date: datetime | None = None) -> Decimal:
        """From Forecast to Completion Cost in the Cost Report"""
        if not date:
            date = datetime.now()
        forecasts = self.forecasts.filter(
            period__month=date.month,
            period__year=date.year,
            status=Forecast.Status.APPROVED,
        )
        return sum_queryset(forecasts, "forecast_transactions__total_price")

    def earned_value(self, date: datetime | None = None) -> Decimal | None:
        """Earned Value = (Actual Cost / Forecast Cost) * Budgeted Amount (Total Contract Value)"""
        if not date:
            date = datetime.now()
        actual = self.actual_cost(date)
        forecast = self.forecast_cost(date)
        if not forecast or forecast == 0:
            return None
        budget = self.get_total_contract_value
        if not budget or budget == 0:
            return None
        return (actual / forecast) * budget

    # def cost_variance(self, date) -> Decimal:
    #     """Earned Value - Actual Cost"""
    #     raise NotImplementedError

    # def schedule_variance(self, date) -> Decimal:
    #     """Earned Value - Planned Value"""
    #     raise NotImplementedError

    def cost_performance_index(
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
        earned = self.earned_value(date)
        actual = self.actual_cost(date)
        if not earned or not actual or actual == 0:
            return None
        return round(earned / actual, 2)

    def schedule_performance_index(
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
        earned = self.earned_value(date)
        planned = self.planned_value(date)
        if not earned or not planned or planned == 0:
            return None
        return round(earned / planned, 2)
