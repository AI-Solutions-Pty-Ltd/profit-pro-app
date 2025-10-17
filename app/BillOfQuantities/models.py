from decimal import Decimal

from django.db import models
from django.db.models import Sum, Q
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
        project = payment_certificate.project
        project = project.line_items.select_related(
            "structure",
            "bill",
            "package",
        ).annotate(
            # Sum transactions from previous approved certificates only
            previous_claimed=Sum(
                "actual_transactions__total_price",
                filter=Q(
                    actual_transactions__payment_certificate__certificate_number__lt=payment_certificate.certificate_number,
                ),
            ),
            previous_qty=Sum(
                "actual_transactions__quantity",
                filter=Q(
                    actual_transactions__payment_certificate__certificate_number__lt=payment_certificate.certificate_number,
                ),
            ),
            # Sum transactions from current certificate only
            current_claim=Sum(
                "actual_transactions__total_price",
                filter=Q(
                    actual_transactions__payment_certificate=payment_certificate,
                ),
            ),
            current_qty=Sum(
                "actual_transactions__quantity",
                filter=Q(
                    actual_transactions__payment_certificate=payment_certificate,
                ),
            ),
            # Sum all claimed transactions up to and including current
            total_claimed=Sum(
                "actual_transactions__total_price",
                filter=Q(
                    actual_transactions__payment_certificate__certificate_number__lte=payment_certificate.certificate_number,
                ),
            ),
            total_qty=Sum(
                "actual_transactions__quantity",
                filter=Q(
                    actual_transactions__payment_certificate__certificate_number__lte=payment_certificate.certificate_number,
                ),
            ),
        )
        return project

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

    class Meta:
        verbose_name = "Payment Certificate"
        verbose_name_plural = "Payment Certificates"
        ordering = ["-created_at"]

    def __str__(self):
        return f"# {self.certificate_number}: {self.project} - {self.status}"

    @staticmethod
    def get_next_certificate_number(project: Project) -> int:
        total_payment_certificates = PaymentCertificate.objects.filter(
            project=project
        ).count()
        return total_payment_certificates + 1

    @property
    def previous_certificates(self) -> list["PaymentCertificate"]:
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

    def __str__(self):
        return f"{self.line_item} - {self.quantity}"
