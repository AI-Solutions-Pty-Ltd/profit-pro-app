from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.db import models
from django.db.models import DecimalField, QuerySet, Value
from django.db.models.functions import Coalesce

from app.Account.models import Account
from app.core.Utilities.models import BaseModel, sum_queryset

if TYPE_CHECKING:
    from app.Project.models import Project


class PaymentCertificate(BaseModel):
    """Used to send to clients for payment"""

    def upload_to(self, filename):
        import os

        base_filename = os.path.basename(filename)
        return f"payment_certificates/{self.project.name}/{base_filename}"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SIGNATORIES_APPROVED = "SIGNATORIES_APPROVED", "Signatories Approved"

    project = models.ForeignKey(
        "Project.Project", on_delete=models.CASCADE, related_name="payment_certificates"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
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
    assessment_date = models.DateTimeField(blank=True, null=True)

    # files
    pdf = models.FileField(upload_to=upload_to, blank=True, null=True)
    abridged_pdf = models.FileField(upload_to=upload_to, blank=True, null=True)
    xlsx = models.FileField(upload_to=upload_to, blank=True, null=True)
    abridged_xlsx = models.FileField(upload_to=upload_to, blank=True, null=True)

    # Generation status tracking
    pdf_generating = models.BooleanField(default=False)
    abridged_pdf_generating = models.BooleanField(default=False)
    xlsx_generating = models.BooleanField(default=False)
    abridged_xlsx_generating = models.BooleanField(default=False)

    if TYPE_CHECKING:
        # Type hint for reverse relationship from ActualTransaction
        actual_transactions: QuerySet[ActualTransaction]
        photos: QuerySet[PaymentCertificatePhoto]
        workings: QuerySet[PaymentCertificateWorking]

    class Meta:
        verbose_name = "Payment Certificate"
        verbose_name_plural = "Payment Certificates"
        ordering = ["-certificate_number"]
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
        if not self.certificate_number:
            self.certificate_number = self.get_next_certificate_number(self.project)

        super().save(*args, **kwargs)

    @staticmethod
    def validate_certificate_numbers(project):
        payment_certificates = PaymentCertificate.objects.filter(
            project=project
        ).order_by("certificate_number")

        for i, payment_certificate in enumerate(payment_certificates):
            if not payment_certificate.certificate_number == i + 1:
                payment_certificate.certificate_number = i + 1
                payment_certificate.save()

    @staticmethod
    def get_next_certificate_number(project: Project) -> int:
        PaymentCertificate.validate_certificate_numbers(project)
        total_payment_certificates = (
            PaymentCertificate.objects.filter(project=project).count() + 1
        )
        if PaymentCertificate.objects.filter(
            project=project, certificate_number=total_payment_certificates
        ).exists():
            raise ValueError(
                f"Certificate with Certificate number: {total_payment_certificates} already exists.\nPlease contact an administrator to remedy."
            )
        return total_payment_certificates

    @property
    def previous_certificates(self) -> QuerySet[PaymentCertificate]:
        return PaymentCertificate.objects.filter(
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
    # grand totals
    #####
    @property
    def contractual_work_plus_special_items_progressive_previous(self) -> Decimal:
        return (
            self.contractual_special_items_progressive_previous
            + self.contract_progressive_previous
        )

    @property
    def contractual_work_plus_special_items_current_claim_total(self) -> Decimal:
        return (
            self.contractual_special_items_current_claim_total
            + self.contract_current_claim_total
        )

    @property
    def contractual_work_plus_special_items_progressive_to_date(self) -> Decimal:
        return (
            self.contractual_special_items_progressive_to_date
            + self.contract_progressive_to_date
        )

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
    def special_items_budget_total(self) -> Decimal:
        """Get budget total of all project special line items."""
        return sum_queryset(self.project.get_special_line_items, "total_price")

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
        """Total amount submitted for payment (Work Items + Ledger Adjustments)."""
        total = Decimal("0.00")
        total += self.items_submitted
        total += self.ledger_current_net_total
        return total

    @property
    def total_certified_amount(self) -> Decimal:
        """Alias for total_submitted to be used in financial reporting."""
        return self.total_submitted

    @property
    def total_claimed(self) -> Decimal:
        """Total amount claimed for payment (Work Items + Ledger Adjustments)."""
        total = Decimal("0.00")
        total += self.items_claimed
        total += self.ledger_current_net_total
        return total

    # wholistic properties
    @property
    def progressive_previous(self) -> Decimal:
        """Calculate total of all previously approved certificates."""
        previous_certificates = self.previous_certificates
        actual_transactions = ActualTransaction.objects.filter(
            payment_certificate__in=previous_certificates
        )
        return sum_queryset(actual_transactions, "total_price")

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

    @property
    def ledger_current_net_total(self) -> Decimal:
        """Calculate the net total of all ledger adjustments for this certificate."""
        total = Decimal("0.00")
        # Models: AdvancePayment, Retention, MaterialsOnSite, Escalation, SpecialItemTransaction
        for attr in [
            "advancepayment_transactions",
            "retention_transactions",
            "materialsonsite_transactions",
            "escalation_transactions",
            "specialitemtransaction_transactions",
        ]:
            if hasattr(self, attr):
                items = getattr(self, attr).all()
                for item in items:
                    total += item.signed_amount
        return total

    @property
    def ledger_progressive_previous(self) -> Decimal:
        """Calculate net total of ledger adjustments from previous approved certificates."""
        total = Decimal("0.00")
        previous_certs = self.previous_certificates
        from .ledger_models import (
            AdvancePayment,
            Escalation,
            MaterialsOnSite,
            Retention,
            SpecialItemTransaction,
        )

        models_to_sum = [
            AdvancePayment,
            Retention,
            MaterialsOnSite,
            Escalation,
            SpecialItemTransaction,
        ]
        for model in models_to_sum:
            transactions = model.objects.filter(
                payment_certificate__in=previous_certs,
            )
            for item in transactions:
                total += item.signed_amount
        return total

    @property
    def ledger_progressive_to_date(self) -> Decimal:
        """Calculate progressive net total of ledger adjustments up to this certificate."""
        return self.ledger_progressive_previous + self.ledger_current_net_total

    @property
    def grand_total_progressive_previous(self) -> Decimal:
        """Total project value certified up to (but not including) this certificate (Work Items + Ledger Adjustments)."""
        return self.progressive_previous + self.ledger_progressive_previous

    @property
    def grand_total_progressive_to_date(self) -> Decimal:
        """The total project value certified to date (Work Items + Ledger Adjustments)."""
        return self.progressive_to_date + self.ledger_progressive_to_date

    @property
    def addendum_budget_total(self) -> Decimal:
        """Get budget total of all project addendum line items."""
        return sum_queryset(
            self.project.line_items.filter(addendum=True).exclude(special_item=True),
            "total_price",
        )

    @property
    def contractual_special_items_progressive_previous(self) -> Decimal:
        """Sum of progressive previous amounts for Addendums, Special Items, and Ledger Totals."""
        return (
            self.addendum_progressive_previous
            + self.special_items_progressive_previous
            + self.ledger_progressive_previous
        )

    @property
    def contractual_special_items_current_claim_total(self) -> Decimal:
        """Sum of current claim totals for Addendums, Special Items, and Ledger Totals."""
        return (
            self.addendum_current_claim_total
            + self.special_items_current_claim_total
            + self.ledger_current_net_total
        )

    @property
    def contractual_special_items_progressive_to_date(self) -> Decimal:
        """Sum of progressive to date totals for Addendums, Special Items, and Ledger Totals."""
        return (
            self.addendum_progressive_to_date
            + self.special_items_progressive_to_date
            + self.ledger_progressive_to_date
        )

    @property
    def has_contractual_special_items(self) -> bool:
        """Return True if the certificate contains any Addendum, Special Items, or Ledger Adjustments."""
        if self.project.line_items.filter(
            models.Q(addendum=True) | models.Q(special_item=True)
        ).exists():
            return True

        for attr in [
            "advancepayment_transactions",
            "retention_transactions",
            "materialsonsite_transactions",
            "escalation_transactions",
            "specialitemtransaction_transactions",
        ]:
            if hasattr(self, attr) and getattr(self, attr).exists():
                return True

        if self.ledger_progressive_previous != 0:
            return True

        return False

    def get_ledger_summary_items(self) -> list[dict[str, Any]]:
        """Get list of ledger summary items with description, previous, current, and total amounts."""
        items = []

        # Advance Payments
        ap_current = self.get_advance_payment_total()
        ap_prev = self.previous_advance_payment_total
        if ap_current != 0 or ap_prev != 0:
            items.append(
                {
                    "description": "Advance Payments",
                    "previous_amount": ap_prev,
                    "current_amount": ap_current,
                    "total_amount": ap_prev + ap_current,
                }
            )

        # Retention
        ret_current = self.get_retention_total()
        ret_prev = self.previous_retention_total
        if ret_current != 0 or ret_prev != 0:
            items.append(
                {
                    "description": "Retention",
                    "previous_amount": ret_prev,
                    "current_amount": ret_current,
                    "total_amount": ret_prev + ret_current,
                }
            )

        # Materials on Site
        mat_current = self.get_materials_on_site_total()
        mat_prev = self.previous_materials_on_site_total
        if mat_current != 0 or mat_prev != 0:
            items.append(
                {
                    "description": "Materials on Site",
                    "previous_amount": mat_prev,
                    "current_amount": mat_current,
                    "total_amount": mat_prev + mat_current,
                }
            )

        # Escalation
        esc_current = self.get_escalation_total()
        esc_prev = self.previous_escalation_total
        if esc_current != 0 or esc_prev != 0:
            items.append(
                {
                    "description": "Escalation",
                    "previous_amount": esc_prev,
                    "current_amount": esc_current,
                    "total_amount": esc_prev + esc_current,
                }
            )

        # Special Items (from SpecialItemTransaction ledger model)
        totals_by_type = self.get_special_item_totals_by_type()
        prev_totals_by_type = self.previous_special_item_totals_by_type
        from .ledger_models import SpecialItemTransaction

        special_item_choices = dict(SpecialItemTransaction.SpecialItemType.choices)
        for item_type, current in totals_by_type.items():
            prev = prev_totals_by_type.get(item_type, Decimal("0.00"))
            if current != 0 or prev != 0:
                label = special_item_choices.get(item_type, item_type)
                items.append(
                    {
                        "description": label,
                        "previous_amount": prev,
                        "current_amount": current,
                        "total_amount": prev + current,
                    }
                )

        return items

    # Helper functions for ledger totals
    def get_advance_payment_total(self) -> Decimal:
        """Get total advance payment transactions for this certificate."""
        from .ledger_models import AdvancePayment

        advance_payments = AdvancePayment.objects.filter(payment_certificate=self)
        debits = advance_payments.filter(
            transaction_type=AdvancePayment.TransactionType.DEBIT
        )
        credits_txn = advance_payments.filter(
            transaction_type=AdvancePayment.TransactionType.CREDIT
        )
        return sum_queryset(debits, "amount") - sum_queryset(credits_txn, "amount")

    def get_retention_total(self) -> Decimal:
        """Get total retention transactions for this certificate."""
        from .ledger_models import Retention

        retention_items = Retention.objects.filter(payment_certificate=self)
        debits = retention_items.filter(
            transaction_type=Retention.TransactionType.DEBIT
        )
        credits_txn = retention_items.filter(
            transaction_type=Retention.TransactionType.CREDIT
        )
        return sum_queryset(debits, "amount") - sum_queryset(credits_txn, "amount")

    def get_materials_on_site_total(self) -> Decimal:
        """Get total materials on site transactions for this certificate."""
        from .ledger_models import MaterialsOnSite

        materials = MaterialsOnSite.objects.filter(payment_certificate=self)
        debits = materials.filter(
            transaction_type=MaterialsOnSite.TransactionType.DEBIT
        )
        credits_txn = materials.filter(
            transaction_type=MaterialsOnSite.TransactionType.CREDIT
        )
        return sum_queryset(debits, "amount") - sum_queryset(credits_txn, "amount")

    def get_escalation_total(self) -> Decimal:
        """Get total escalation transactions for this certificate."""
        from .ledger_models import Escalation

        escalations = Escalation.objects.filter(payment_certificate=self)
        debits = escalations.filter(transaction_type=Escalation.TransactionType.DEBIT)
        credits_txn = escalations.filter(
            transaction_type=Escalation.TransactionType.CREDIT
        )
        return sum_queryset(debits, "amount") - sum_queryset(credits_txn, "amount")

    def get_special_item_total(self) -> Decimal:
        """Get total special item transactions for this certificate."""
        from .ledger_models import SpecialItemTransaction

        special_items = SpecialItemTransaction.objects.filter(payment_certificate=self)
        debits = special_items.filter(
            transaction_type=SpecialItemTransaction.TransactionType.DEBIT
        )
        credits_txn = special_items.filter(
            transaction_type=SpecialItemTransaction.TransactionType.CREDIT
        )
        return sum_queryset(debits, "amount") - sum_queryset(credits_txn, "amount")

    def get_special_item_totals_by_type(self) -> dict:
        """Get special item totals grouped by type for this certificate."""
        from .ledger_models import SpecialItemTransaction

        totals = {}
        for item_type, _ in SpecialItemTransaction.SpecialItemType.choices:
            items_by_type = SpecialItemTransaction.objects.filter(
                payment_certificate=self, special_item_type=item_type
            )
            debits = items_by_type.filter(
                transaction_type=SpecialItemTransaction.TransactionType.DEBIT
            )
            credits_txn = items_by_type.filter(
                transaction_type=SpecialItemTransaction.TransactionType.CREDIT
            )
            totals[item_type] = sum_queryset(debits, "amount") - sum_queryset(
                credits_txn, "amount"
            )

        return totals

    def get_all_ledger_totals(self) -> dict:
        """Get all ledger totals for this certificate."""
        return {
            "advance_payments": self.get_advance_payment_total(),
            "retention": self.get_retention_total(),
            "materials_on_site": self.get_materials_on_site_total(),
            "escalation": self.get_escalation_total(),
            "special_items": self.get_special_item_total(),
            "special_items_by_type": self.get_special_item_totals_by_type(),
        }

    # Helper functions for previous certificate totals
    @property
    def previous_advance_payment_total(self) -> Decimal:
        """Get total advance payment transactions from previous certificates."""
        from .ledger_models import AdvancePayment

        previous_certificates = self.previous_certificates
        advance_payments = AdvancePayment.objects.filter(
            payment_certificate__in=previous_certificates
        )
        debits = advance_payments.filter(
            transaction_type=AdvancePayment.TransactionType.DEBIT
        )
        credits_txn = advance_payments.filter(
            transaction_type=AdvancePayment.TransactionType.CREDIT
        )
        return sum_queryset(debits, "amount") - sum_queryset(credits_txn, "amount")

    @property
    def previous_retention_total(self) -> Decimal:
        """Get total retention transactions from previous certificates."""
        from .ledger_models import Retention

        previous_certificates = self.previous_certificates
        retention_items = Retention.objects.filter(
            payment_certificate__in=previous_certificates
        )
        debits = retention_items.filter(
            transaction_type=Retention.TransactionType.DEBIT
        )
        credits_txn = retention_items.filter(
            transaction_type=Retention.TransactionType.CREDIT
        )
        return sum_queryset(debits, "amount") - sum_queryset(credits_txn, "amount")

    @property
    def previous_materials_on_site_total(self) -> Decimal:
        """Get total materials on site transactions from previous certificates."""
        from .ledger_models import MaterialsOnSite

        previous_certificates = self.previous_certificates
        materials = MaterialsOnSite.objects.filter(
            payment_certificate__in=previous_certificates
        )
        debits = materials.filter(
            transaction_type=MaterialsOnSite.TransactionType.DEBIT
        )
        credits_txn = materials.filter(
            transaction_type=MaterialsOnSite.TransactionType.CREDIT
        )
        return sum_queryset(debits, "amount") - sum_queryset(credits_txn, "amount")

    @property
    def previous_escalation_total(self) -> Decimal:
        """Get total escalation transactions from previous certificates."""
        from .ledger_models import Escalation

        previous_certificates = self.previous_certificates
        escalations = Escalation.objects.filter(
            payment_certificate__in=previous_certificates
        )
        debits = escalations.filter(transaction_type=Escalation.TransactionType.DEBIT)
        credits_txn = escalations.filter(
            transaction_type=Escalation.TransactionType.CREDIT
        )
        return sum_queryset(debits, "amount") - sum_queryset(credits_txn, "amount")

    @property
    def previous_special_item_total(self) -> Decimal:
        """Get total special item transactions from previous certificates."""
        from .ledger_models import SpecialItemTransaction

        previous_certificates = self.previous_certificates
        special_items = SpecialItemTransaction.objects.filter(
            payment_certificate__in=previous_certificates
        )
        debits = special_items.filter(
            transaction_type=SpecialItemTransaction.TransactionType.DEBIT
        )
        credits_txn = special_items.filter(
            transaction_type=SpecialItemTransaction.TransactionType.CREDIT
        )
        return sum_queryset(debits, "amount") - sum_queryset(credits_txn, "amount")

    @property
    def previous_special_item_totals_by_type(self) -> dict:
        """Get special item totals grouped by type from previous certificates."""
        from .ledger_models import SpecialItemTransaction

        previous_certificates = self.previous_certificates

        totals = {}
        for item_type, _ in SpecialItemTransaction.SpecialItemType.choices:
            items_by_type = SpecialItemTransaction.objects.filter(
                payment_certificate__in=previous_certificates,
                special_item_type=item_type,
            )
            debits = items_by_type.filter(
                transaction_type=SpecialItemTransaction.TransactionType.DEBIT
            )
            credits_txn = items_by_type.filter(
                transaction_type=SpecialItemTransaction.TransactionType.CREDIT
            )
            totals[item_type] = sum_queryset(debits, "amount") - sum_queryset(
                credits_txn, "amount"
            )

        return totals


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
        if self.payment_certificate.xlsx:
            # reset xlsx as it needs to be regenerated
            self.payment_certificate.xlsx = None
        if self.payment_certificate.abridged_xlsx:
            # reset abridged xlsx as it needs to be regenerated
            self.payment_certificate.abridged_xlsx = None
        self.payment_certificate.save()
        super().save(*args, **kwargs)


class Signatory(BaseModel):
    payment_certificate = models.ForeignKey(
        PaymentCertificate,
        on_delete=models.CASCADE,
        related_name="signatories",
    )
    signatory = models.ForeignKey(
        "Project.Signatories",
        on_delete=models.CASCADE,
        related_name="signatories",
    )
    approved = models.BooleanField(default=False)
    comments = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Signatory"
        verbose_name_plural = "Signatories"
        ordering = ["payment_certificate"]
        indexes = [
            models.Index(fields=["payment_certificate", "signatory"]),
            models.Index(fields=["signatory", "approved"]),
        ]

    def __str__(self):
        return f"{self.signatory} - {self.payment_certificate}"


class PaymentCertificatePhoto(BaseModel):
    """Photos attached to a payment certificate."""

    def upload_to(self, filename):
        import os

        base_filename = os.path.basename(filename)
        return f"payment_certificates/{self.payment_certificate.project.name}/photos/{base_filename}"

    payment_certificate = models.ForeignKey(
        PaymentCertificate,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    title = models.CharField(
        max_length=255,
        help_text="Photo title or description",
    )
    image = models.ImageField(
        upload_to=upload_to,
        help_text="Upload photo file",
    )
    uploaded_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Payment Certificate Photo"
        verbose_name_plural = "Payment Certificate Photos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.payment_certificate}"


class PaymentCertificateWorking(BaseModel):
    """Working documents attached to a payment certificate."""

    def upload_to(self, filename):
        import os

        base_filename = os.path.basename(filename)
        return f"payment_certificates/{self.payment_certificate.project.name}/workings/{base_filename}"

    payment_certificate = models.ForeignKey(
        PaymentCertificate,
        on_delete=models.CASCADE,
        related_name="workings",
    )
    title = models.CharField(
        max_length=255,
        help_text="Document title or description",
    )
    file = models.FileField(
        upload_to=upload_to,
        help_text="Upload working document",
    )
    uploaded_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Payment Certificate Working"
        verbose_name_plural = "Payment Certificate Workings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.payment_certificate}"
