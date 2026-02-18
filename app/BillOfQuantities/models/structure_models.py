from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import DecimalField, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse

from app.core.Utilities.models import BaseModel, sum_queryset

from .payment_certificate_models import ActualTransaction, PaymentCertificate

if TYPE_CHECKING:
    from app.Cost.models import Cost
    from app.Project.models import Project

    from .forecast_models import Forecast


class Structure(BaseModel):
    """Structure model representing buildings/structures within a project."""

    project = models.ForeignKey(
        "Project.Project", on_delete=models.CASCADE, related_name="structures"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    if TYPE_CHECKING:
        line_items: QuerySet[LineItem]
        bills: QuerySet[Bill]

    class Meta:
        verbose_name = "Structure"
        verbose_name_plural = "Structures"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.project.name})"

    def get_absolute_url(self):
        return reverse(
            "bill_of_quantities:structure-detail",
            kwargs={"project_pk": self.project.pk, "pk": self.pk},
        )

    def get_update_url(self):
        return reverse(
            "bill_of_quantities:structure-update",
            kwargs={"project_pk": self.project.pk, "pk": self.pk},
        )

    def get_delete_url(self):
        return reverse(
            "bill_of_quantities:structure-delete",
            kwargs={"project_pk": self.project.pk, "pk": self.pk},
        )

    @property
    def budget_total(self) -> Decimal:
        """Get total budget for all line items in this structure."""
        return self.line_items.filter(is_work=True, special_item=False).aggregate(
            total=Coalesce(Sum("total_price"), Value(Decimal("0.00")))
        )["total"]

    def get_total_line_items(self) -> int:
        """Get total number of line items in this structure."""
        return self.line_items.count()

    def get_total_value(self) -> Decimal:
        """Get total value of all line items in this structure."""
        return self.line_items.aggregate(
            total=Coalesce(Sum("total_price"), Value(Decimal("0.00")))
        )["total"]

    def get_forecast_total(self, forecast: Forecast) -> Decimal:
        """Get total forecast for all line items in this structure for a specific forecast."""
        from app.BillOfQuantities.models import ForecastTransaction

        return ForecastTransaction.objects.filter(
            forecast=forecast,
            line_item__structure=self,
            line_item__is_work=True,
            line_item__special_item=False,
        ).aggregate(total=Coalesce(Sum("total_price"), Value(Decimal("0.00"))))["total"]

    @staticmethod
    def upload_wbs_csv(project: Project):
        return reverse(
            "bill_of_quantities:structure-upload", kwargs={"project_pk": project.id}
        )


class Bill(BaseModel):
    structure = models.ForeignKey(
        Structure, on_delete=models.CASCADE, related_name="bills"
    )
    name = models.CharField(max_length=100)

    if TYPE_CHECKING:
        line_items: QuerySet[LineItem]
        costs: QuerySet[Cost]

    class Meta:
        verbose_name = "Bill"
        verbose_name_plural = "Bills"

    def __str__(self):
        return self.name

    @property
    def budget_total(self) -> Decimal:
        """Get total budget for all line items in this bill."""
        return self.line_items.filter(is_work=True, special_item=False).aggregate(
            total=Coalesce(Sum("total_price"), Value(Decimal("0.00")))
        )["total"]

    def get_forecast_total(self, forecast: Forecast) -> Decimal:
        """Get total forecast for all line items in this bill for a specific forecast."""
        from app.BillOfQuantities.models import ForecastTransaction

        return ForecastTransaction.objects.filter(
            forecast=forecast,
            line_item__bill=self,
            line_item__is_work=True,
            line_item__special_item=False,
        ).aggregate(total=Coalesce(Sum("total_price"), Value(Decimal("0.00"))))["total"]


class Package(BaseModel):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="packages")
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Packages"

    def __str__(self):
        return self.name


class LineItem(BaseModel):
    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    structure = models.ForeignKey(
        Structure,
        on_delete=models.CASCADE,
        related_name="line_items",
        null=True,
        blank=True,
    )
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name="line_items",
        null=True,
        blank=True,
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        related_name="line_items",
        null=True,
        blank=True,
    )
    row_index = models.IntegerField()

    # headings / etc
    item_number = models.CharField(max_length=100, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    # for work line items
    is_work = models.BooleanField(default=False)
    unit_measurement = models.CharField(max_length=10, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    budgeted_quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)

    # for addendum / variations line items
    addendum = models.BooleanField(default=False)
    special_item = models.BooleanField(default=False)

    if TYPE_CHECKING:
        actual_transactions: QuerySet[ActualTransaction]

    class Meta:
        verbose_name = "Line Item"
        verbose_name_plural = "Line Items"
        ordering = ["row_index"]

    def __str__(self):
        parts = []
        if self.item_number:
            parts.append(self.item_number)
        if self.structure:
            parts.append(self.structure.name)
        if self.bill:
            parts.append(self.bill.name)
        if self.package:
            parts.append(self.package.name)
        parts.append(self.description or str(self.pk))
        return " - ".join(parts)

    @staticmethod
    def construct_payment_certificate(
        payment_certificate: PaymentCertificate,
    ):
        """
        Construct optimized queryset of line items with payment certificate data.

        Performance optimizations:
        - Uses select_related to avoid N+1 queries on ForeignKeys
        - Uses only() to fetch only required fields
        - Uses Coalesce to handle NULL values from annotations
        - Filters to only include line items with transactions in current certificate
        """
        project: Project = payment_certificate.project
        cert_number = payment_certificate.certificate_number

        return (
            project.get_line_items.only(
                # LineItem fields
                "id",
                "item_number",
                "description",
                "unit_price",
                "unit_measurement",
                "budgeted_quantity",
                "total_price",
                "row_index",
                # Structure fields
                "structure__id",
                "structure__name",
                # Bill fields
                "bill__id",
                "bill__name",
                # Package fields
                "package__id",
                "package__name",
            )
            .annotate(
                # Use Coalesce to return 0 instead of None for NULL aggregations
                previous_qty=Coalesce(
                    Sum(
                        "actual_transactions__quantity",
                        filter=Q(
                            actual_transactions__payment_certificate__certificate_number__lt=cert_number,
                            actual_transactions__payment_certificate__status=PaymentCertificate.Status.APPROVED,
                        ),
                    ),
                    Value(0),
                    output_field=DecimalField(),
                ),
                current_qty=Coalesce(
                    Sum(
                        "actual_transactions__quantity",
                        filter=Q(
                            actual_transactions__payment_certificate=payment_certificate,
                        ),
                    ),
                    Value(0),
                    output_field=DecimalField(),
                ),
                total_qty=Coalesce(
                    Sum(
                        "actual_transactions__quantity",
                        filter=Q(
                            actual_transactions__payment_certificate__certificate_number__lte=cert_number,
                        ),
                    ),
                    Value(0),
                    output_field=DecimalField(),
                ),
                previous_claimed=Coalesce(
                    Sum(
                        "actual_transactions__total_price",
                        filter=Q(
                            actual_transactions__payment_certificate__certificate_number__lt=cert_number,
                            actual_transactions__payment_certificate__status=PaymentCertificate.Status.APPROVED,
                        ),
                    ),
                    Value(0),
                    output_field=DecimalField(),
                ),
                current_claim=Coalesce(
                    Sum(
                        "actual_transactions__total_price",
                        filter=Q(
                            actual_transactions__payment_certificate=payment_certificate,
                        ),
                    ),
                    Value(0),
                    output_field=DecimalField(),
                ),
                total_claimed=Coalesce(
                    Sum(
                        "actual_transactions__total_price",
                        filter=Q(
                            actual_transactions__payment_certificate__certificate_number__lte=cert_number,
                        ),
                    ),
                    Value(0),
                    output_field=DecimalField(),
                ),
            )
            .distinct()
        )

    @staticmethod
    def abridged_payment_certificate(payment_certificate):
        """
        Construct abridged queryset of line items with only claimed items.

        This method builds on construct_payment_certificate and filters to only
        include line items where current_claim > 0 (items with actual monetary claims).

        Note: This excludes non-work items (headings) and items with zero claims.
        Use construct_payment_certificate() if you need all line items including headings.

        Args:
            payment_certificate: PaymentCertificate instance

        Returns:
            QuerySet: Filtered line items with current_claim > 0
        """
        line_items = LineItem.construct_payment_certificate(payment_certificate)
        return line_items.exclude(current_claim=0)

    @property
    def claimed_to_date(self) -> Decimal:
        # historically qty claimed, excluding current pmt cert
        project: Project = self.project
        active_payment_certificate: PaymentCertificate | None = (
            project.active_payment_certificate
        )

        actual_transactions = self.actual_transactions.filter(claimed=True)

        if active_payment_certificate:
            current_transactions_ids = (
                active_payment_certificate.actual_transactions.values_list(
                    "id", flat=True
                )
            )
            actual_transactions = actual_transactions.exclude(
                id__in=current_transactions_ids
            )
        return sum_queryset(actual_transactions, "quantity")

    @property
    def claimed_to_date_value(self) -> Decimal:
        # historically claim value, excluding current pmt cert
        project: Project = self.project
        active_payment_certificate: PaymentCertificate | None = (
            project.active_payment_certificate
        )
        if active_payment_certificate:
            previous_actual_transactions = self.actual_transactions.filter(
                payment_certificate__certificate_number__lt=active_payment_certificate.certificate_number
            )
        else:
            previous_actual_transactions = self.actual_transactions
        return sum_queryset(previous_actual_transactions, "total_price")

    @property
    def remaining_quantity(self):
        # remaining quantity, excluding current pmt cert
        total_claimed = self.claimed_to_date
        budgeted_quantity = self.budgeted_quantity or Decimal(0)
        return budgeted_quantity - total_claimed

    @property
    def current_transaction(self):
        project: Project = self.project
        active_certificate = project.active_payment_certificate
        if active_certificate:
            try:
                return active_certificate.actual_transactions.get(
                    payment_certificate=active_certificate,
                    line_item=self,
                )
            except Exception as _:
                pass
        return None

    @property
    def total_claimed_to_date(self):
        return sum_queryset(self.actual_transactions, "total_price")
