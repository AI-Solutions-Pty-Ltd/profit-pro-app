from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import DecimalField, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
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
        Project, on_delete=models.CASCADE, related_name="line_items"
    )
    structure = models.ForeignKey(
        Structure, on_delete=models.CASCADE, related_name="line_items"
    )
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="line_items")
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

    class Meta:
        verbose_name = "Line Item"
        verbose_name_plural = "Line Items"
        ordering = ["row_index"]

    def __str__(self):
        return self.item_number

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
        project = payment_certificate.project
        cert_number = payment_certificate.certificate_number
        line_items = project.line_items.all()

        return (
            line_items.select_related(
                "structure",
                "bill",
                "package",
            )
            .only(
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
        # historically claim, excluding current pmt cert
        project: Project = self.project
        active_payment_certificate: PaymentCertificate = (
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
        value = (
            actual_transactions.aggregate(total=models.Sum("quantity"))["total"] or 0
        )
        return Decimal(value)

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
        return PaymentCertificate.objects.filter(
            project=self.project,
            certificate_number__lt=self.certificate_number,
            status=PaymentCertificate.Status.APPROVED,
        )

    @property
    def total_amount(self) -> Decimal:
        total_amount = (
            self.actual_transactions.aggregate(total=models.Sum("total_price"))["total"]
            or 0
        )
        return Decimal(total_amount)

    @property
    def items_submitted(self) -> Decimal:
        approved_line_items = self.actual_transactions.filter(approved=True)
        total_submitted = (
            approved_line_items.aggregate(total=models.Sum("total_price"))["total"] or 0
        )
        return Decimal(total_submitted)

    @property
    def items_claimed(self) -> Decimal:
        approved_line_items = self.actual_transactions.filter(claimed=True)
        total_claimed = (
            approved_line_items.aggregate(total=models.Sum("total_price"))["total"] or 0
        )
        return Decimal(total_claimed)

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

    @property
    def progressive_previous(self) -> Decimal:
        """Calculate total of all previously approved certificates."""
        previous_certificates = self.previous_certificates
        total = (
            previous_certificates.aggregate(
                total=models.Sum("actual_transactions__total_price")
            )["total"]
            or 0
        )
        return Decimal(total)

    @property
    def current_claim_total(self) -> Decimal:
        """Calculate total for current certificate (all transactions)."""
        current_claim_total = (
            self.actual_transactions.aggregate(total=models.Sum("total_price"))["total"]
            or 0
        )
        return Decimal(current_claim_total)

    @property
    def progressive_to_date(self) -> Decimal:
        """Calculate progressive total including this certificate."""
        # For progressive to date, we include all transactions in current certificate
        # regardless of approval status (for reporting purposes)
        return self.progressive_previous + self.current_claim_total


class ActualTransaction(BaseModel):
    """Capture actual work completed against a line item"""

    payment_certificate = models.ForeignKey(
        PaymentCertificate, on_delete=models.CASCADE, related_name="actual_transactions"
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
        return f"{self.line_item} - {self.quantity}"

    def save(self, *args, **kwargs):
        if self.payment_certificate.pdf:
            self.payment_certificate.pdf = None
        if self.payment_certificate.abridged_pdf:
            self.payment_certificate.abridged_pdf = None
        self.payment_certificate.save()
        super().save(*args, **kwargs)
