from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from django.db import models
from django.db.models import QuerySet
from django.urls import reverse

from app.Account.models import Account
from app.core.Utilities.models import BaseModel, sum_queryset

if TYPE_CHECKING:
    from app.BillOfQuantities.models import Forecast, LineItem, PaymentCertificate

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
        return self.projects.filter(status=Project.Status.ACTIVE)

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


class Project(BaseModel):
    class Status(models.TextChoices):
        SETUP = "SETUP", "Setup"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

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

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )

    if TYPE_CHECKING:
        payment_certificates: QuerySet[PaymentCertificate]
        line_items: QuerySet[LineItem]
        forecasts: QuerySet[Forecast]
        signatories: QuerySet["Signatories"] | None
        planned_values: QuerySet["PlannedValue"] | None

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-name"]

    def get_absolute_url(self):
        return reverse("project:project-detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse("project:project-list")

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
        from app.BillOfQuantities.models import PaymentCertificate

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
