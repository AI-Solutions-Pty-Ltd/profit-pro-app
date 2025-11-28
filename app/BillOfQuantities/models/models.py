from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import DecimalField, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse

from app.Account.models import Account
from app.core.Utilities.models import BaseModel, sum_queryset
from app.Project.models import Project


class Structure(BaseModel):
    """Structure model representing buildings/structures within a project."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="structures"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Structure"
        verbose_name_plural = "Structures"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.project.name})"

    def get_absolute_url(self):
        return reverse(
            "bill_of_quantities:structure-detail",
            kwargs={"pk": self.pk},
        )

    def get_update_url(self):
        return reverse(
            "bill_of_quantities:structure-update",
            kwargs={"pk": self.pk},
        )

    def get_delete_url(self):
        return reverse(
            "bill_of_quantities:structure-delete",
            kwargs={"pk": self.pk},
        )

    @property
    def budget_total(self) -> Decimal:
        """Get total budget for all line items in this structure."""
        return self.line_items.filter(is_work=True, special_item=False).aggregate(
            total=Coalesce(Sum("total_price"), Value(Decimal("0.00")))
        )["total"]

    def get_forecast_total(self, forecast: "Forecast") -> Decimal:
        """Get total forecast for all line items in this structure for a specific forecast."""
        from app.BillOfQuantities.models import ForecastTransaction

        return ForecastTransaction.objects.filter(
            forecast=forecast,
            line_item__structure=self,
            line_item__is_work=True,
            line_item__special_item=False,
        ).aggregate(total=Coalesce(Sum("total_price"), Value(Decimal("0.00"))))["total"]


class Bill(BaseModel):
    structure = models.ForeignKey(
        Structure, on_delete=models.CASCADE, related_name="bills"
    )
    name = models.CharField(max_length=100)

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

    def get_forecast_total(self, forecast: "Forecast") -> Decimal:
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
        Project,
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

    # for addendum line items
    addendum = models.BooleanField(default=False)
    special_item = models.BooleanField(default=False)

    if TYPE_CHECKING:
        actual_transactions: QuerySet["ActualTransaction"]

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
        payment_certificate: "PaymentCertificate",
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
            project.get_active_payment_certificate
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
            project.get_active_payment_certificate
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
        active_certificate = project.get_active_payment_certificate
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


class PaymentCertificate(BaseModel):
    """Used to send to clients for payment"""

    if TYPE_CHECKING:
        # Type hint for reverse relationship from ActualTransaction
        actual_transactions: QuerySet["ActualTransaction"]

    def upload_to(self, filename):
        return f"payment_certificates/{self.project.name}/{filename}"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="payment_certificates"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )

    certificate_number = models.IntegerField()
    notes = models.TextField(
        blank=True, default="", help_text="Additional notes or comments"
    )
    approved_on = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True
    )

    # files
    pdf = models.FileField(upload_to=upload_to, blank=True, null=True)
    abridged_pdf = models.FileField(upload_to=upload_to, blank=True, null=True)

    # PDF generation status tracking
    pdf_generating = models.BooleanField(default=False)
    abridged_pdf_generating = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Payment Certificate"
        verbose_name_plural = "Payment Certificates"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["certificate_number", "status"]),
            models.Index(fields=["project", "certificate_number"]),
        ]
        unique_together = ("project", "certificate_number")

    def __str__(self):
        return f"# {self.certificate_number}: {self.project} - {self.status}"

    @staticmethod
    def get_next_certificate_number(project: Project) -> int:
        total_payment_certificates = PaymentCertificate.objects.filter(
            project=project
        ).count()
        return total_payment_certificates + 1

    @property
    def previous_certificates(self) -> QuerySet["PaymentCertificate"]:
        return PaymentCertificate.all_objects.filter(
            project=self.project,
            certificate_number__lt=self.certificate_number,
            status=PaymentCertificate.Status.APPROVED,
        )

    #####
    # related actual transactions getters
    #####
    @property
    def all_actual_transactions(self):
        """get actual transactions linked to this payment certificate"""
        return self.actual_transactions.all()

    @property
    def contract_actual_items(self):
        """get contract actual transactions linked to this payment certificate"""
        return self.all_actual_transactions.filter(
            line_item__special_item=False, line_item__addendum=False
        )

    @property
    def addendum_actual_items(self):
        """get addendum actual transactions linked to this payment certificate"""
        return self.all_actual_transactions.filter(
            line_item__special_item=False, line_item__addendum=True
        )

    @property
    def special_actual_items(self):
        """get special actual transactions linked to this payment certificate"""
        special_items = self.all_actual_transactions.filter(
            line_item__special_item=True
        )
        return special_items

    #####
    # contract line_items summary
    #####
    @property
    def contract_progressive_previous(self) -> Decimal:
        """get all previously claimed contract actual transactions"""
        previous_certificates = self.previous_certificates
        previous_actual_items = ActualTransaction.objects.filter(
            payment_certificate__in=previous_certificates
        ).exclude(line_item__special_item=True)
        return sum_queryset(previous_actual_items, "total_price")

    @property
    def contract_current_claim_total(self) -> Decimal:
        """get all currently claimed contract actual transactions"""
        return sum_queryset(self.contract_actual_items, "total_price")

    @property
    def contract_progressive_to_date(self) -> Decimal:
        """get contract actual transactions total claimed up to payment certificate"""
        return self.contract_progressive_previous + self.contract_current_claim_total

    #####
    # addendum line_items summary
    #####
    @property
    def addendum_progressive_previous(self) -> Decimal:
        """get all previously claimed addendum actual transactions"""
        previous_certificates = self.previous_certificates
        previous_actual_items = ActualTransaction.objects.filter(
            payment_certificate__in=previous_certificates,
            line_item__addendum=True,
        ).exclude(line_item__special_item=True)
        return sum_queryset(previous_actual_items, "total_price")

    @property
    def addendum_current_claim_total(self) -> Decimal:
        """get all currently claimed addendum actual transactions"""
        return sum_queryset(self.addendum_actual_items, "total_price")

    @property
    def addendum_progressive_to_date(self) -> Decimal:
        """get addendum actual transactions total claimed up to payment certificate"""
        return self.addendum_progressive_previous + self.addendum_current_claim_total

    #####
    # contract + addendum
    #####
    @property
    def work_progressive_previous(self) -> Decimal:
        return self.contract_progressive_previous + self.addendum_progressive_previous

    @property
    def work_current_claim_total(self) -> Decimal:
        return self.contract_current_claim_total + self.addendum_current_claim_total

    @property
    def work_progressive_to_date(self) -> Decimal:
        return self.work_progressive_previous + self.work_current_claim_total

    #####
    # special items summary
    #####
    @property
    def special_items_progressive_previous(self):
        previous_certificates = self.previous_certificates
        previous_actual_items = ActualTransaction.objects.filter(
            payment_certificate__in=previous_certificates
        ).filter(line_item__special_item=True)
        return sum_queryset(previous_actual_items, "total_price")

    @property
    def special_items_current_claim_total(self) -> Decimal:
        return sum_queryset(self.special_actual_items, "total_price")

    @property
    def special_items_progressive_to_date(self) -> Decimal:
        return (
            self.special_items_progressive_previous
            + self.special_items_current_claim_total
        )

    @property
    def special_items_annotated(self):
        # annotate all project special items with total_price up to current certificate
        special_items = self.project.get_special_line_items
        return special_items.annotate(
            total=Coalesce(
                models.Sum(
                    "actual_transactions__total_price",
                    filter=models.Q(
                        actual_transactions__payment_certificate__certificate_number__lte=self.certificate_number
                    ),
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(),
            )
        )

    # payment certificate summary
    @property
    def items_submitted(self) -> Decimal:
        approved_line_items = self.all_actual_transactions.filter(approved=True)
        return sum_queryset(approved_line_items, "total_price")

    @property
    def items_claimed(self) -> Decimal:
        approved_line_items = self.all_actual_transactions.filter(claimed=True)
        return sum_queryset(approved_line_items, "total_price")

    @property
    def total_submitted(self) -> Decimal:
        total = Decimal(0)
        total += self.items_submitted
        # leaving space for other categories to be added at a later stage
        return total

    @property
    def total_claimed(self) -> Decimal:
        total = Decimal(0)
        total += self.items_claimed
        # leaving space for other categories to be added at a later stage
        return total

    # wholistic properties
    @property
    def progressive_previous(self) -> Decimal:
        """Calculate total of all previously approved certificates."""
        previous_certificates = self.previous_certificates
        return sum_queryset(previous_certificates, "actual_transactions__total_price")

    @property
    def current_claim_total(self) -> Decimal:
        """Calculate total for current certificate (all actual transactions)."""
        return sum_queryset(self.all_actual_transactions, "total_price")

    @property
    def progressive_to_date(self) -> Decimal:
        """Calculate progressive total up to this certificate."""
        # For progressive to date, we include all transactions in current certificate
        # regardless of approval status (for reporting purposes)
        return self.progressive_previous + self.current_claim_total


class ActualTransaction(BaseModel):
    """Capture actual work completed against a line item"""

    payment_certificate = models.ForeignKey(
        PaymentCertificate,
        on_delete=models.CASCADE,
        related_name="actual_transactions",
    )
    line_item = models.ForeignKey(
        LineItem, on_delete=models.CASCADE, related_name="actual_transactions"
    )

    captured_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        related_name="captured_actual_transactions",
        blank=True,
        null=True,
    )
    approved_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        related_name="approved_actual_transactions",
        blank=True,
        null=True,
    )

    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)

    approved = models.BooleanField(default=False)
    claimed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Actual Transaction"
        verbose_name_plural = "Actual Transactions"
        ordering = ["line_item__row_index"]
        indexes = [
            models.Index(fields=["payment_certificate", "line_item"]),
            models.Index(fields=["line_item", "claimed"]),
        ]

    def __str__(self):
        return f"{self.line_item.description if self.line_item else self.line_item.pk} - {self.quantity}"

    def save(self, *args, **kwargs):
        if self.payment_certificate.pdf:
            # reset pdf as it needs to be regenerated
            self.payment_certificate.pdf = None
        if self.payment_certificate.abridged_pdf:
            # reset abridged pdf as it needs to be regenerated
            self.payment_certificate.abridged_pdf = None
        self.payment_certificate.save()
        super().save(*args, **kwargs)


class Forecast(BaseModel):
    """Capture forecasted work completed against a line item"""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"

    project: Project = models.ForeignKey(  # type: ignore
        Project, on_delete=models.CASCADE, related_name="forecasts"
    )
    period = models.DateField()
    status: Status = models.CharField(  # type: ignore
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    approved_by: Account = models.ForeignKey(  # type: ignore
        Account,
        on_delete=models.SET_NULL,
        related_name="approved_forecasts",
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)

    captured_by: Account = models.ForeignKey(  # type: ignore
        Account,
        on_delete=models.SET_NULL,
        related_name="captured_forecasts",
        blank=True,
        null=True,
    )

    if TYPE_CHECKING:
        forecast_transactions: QuerySet["ForecastTransaction"]

    class Meta:
        verbose_name = "Forecast"
        verbose_name_plural = "Forecasts"
        ordering = ["period"]
        unique_together = [["project", "period"]]
        indexes = [
            models.Index(fields=["project", "period"]),
            models.Index(fields=["period"]),
        ]

    def __str__(self) -> str:
        return f"{self.period} - {self.status}"

    def clean(self) -> None:
        """Normalize period to first day of month (mm-yyyy format)."""
        if self.period:
            self.period = self.period.replace(day=1)

    def save(self, *args, **kwargs) -> None:
        self.clean()
        return super().save(*args, **kwargs)

    @property
    def total_forecast(self) -> Decimal:
        # return total of forecast transactions
        return sum_queryset(self.forecast_transactions, "total_price")


class ForecastTransaction(BaseModel):
    """Capture forecasted work completed against a line item"""

    class Type(models.TextChoices):
        PAYMENT_CERTIFICATE = "PAYMENT_CERTIFICATE", "Payment Certificate"
        FORECAST = "FORECAST", "Forecast"

    forecast: Forecast = models.ForeignKey(  # type: ignore
        Forecast,
        on_delete=models.CASCADE,
        related_name="forecast_transactions",
        blank=True,
        null=True,
    )
    line_item: LineItem = models.ForeignKey(  # type: ignore
        LineItem,
        on_delete=models.CASCADE,
        related_name="forecast_transactions",
        blank=True,
        null=True,
    )

    quantity: Decimal = models.DecimalField(max_digits=10, decimal_places=2)  # type: ignore
    unit_price: Decimal = models.DecimalField(  # type: ignore
        max_digits=10, decimal_places=2, blank=True
    )
    total_price: Decimal = models.DecimalField(  # type: ignore
        max_digits=10, decimal_places=2, blank=True
    )
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.line_item.description if self.line_item else self.line_item.pk} - {self.quantity}"
