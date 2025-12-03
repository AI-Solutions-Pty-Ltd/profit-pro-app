from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import DecimalField, QuerySet, Value
from django.db.models.functions import Coalesce

from app.Account.models import Account
from app.core.Utilities.models import BaseModel, sum_queryset

if TYPE_CHECKING:
    from app.Project.models import Project


class PaymentCertificate(BaseModel):
    """Used to send to clients for payment"""

    if TYPE_CHECKING:
        # Type hint for reverse relationship from ActualTransaction
        actual_transactions: QuerySet[ActualTransaction]

    def upload_to(self, filename):
        return f"payment_certificates/{self.project.name}/{filename}"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    project = models.ForeignKey(
        "Project.Project", on_delete=models.CASCADE, related_name="payment_certificates"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )

    certificate_number = models.IntegerField()
    notes = models.TextField(
        blank=True, default="", help_text="Additional notes or comments"
    )
    is_final = models.BooleanField(
        default=False,
        help_text="Mark as final payment certificate for the project",
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

    def save(self, *args, **kwargs):
        """Override save to update project status when final certificate is approved."""
        # Check if this is an existing record being updated
        if self.pk:
            try:
                old_instance = PaymentCertificate.objects.get(pk=self.pk)
                # If status changed to APPROVED and this is the final certificate
                if (
                    old_instance.status != self.Status.APPROVED
                    and self.status == self.Status.APPROVED
                    and self.is_final
                ):
                    # Update project status to FINAL_ACCOUNT_ISSUED
                    self.project.status = Project.Status.FINAL_ACCOUNT_ISSUED
                    self.project.final_payment_certificate = self
                    self.project.save(
                        update_fields=["status", "final_payment_certificate"]
                    )
            except PaymentCertificate.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    @staticmethod
    def get_next_certificate_number(project: Project) -> int:
        total_payment_certificates = PaymentCertificate.objects.filter(
            project=project
        ).count()
        return total_payment_certificates + 1

    @property
    def previous_certificates(self) -> QuerySet[PaymentCertificate]:
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
        "BillOfQuantities.LineItem",
        on_delete=models.CASCADE,
        related_name="actual_transactions",
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
