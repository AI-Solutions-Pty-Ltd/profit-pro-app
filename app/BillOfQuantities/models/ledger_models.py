"""
Ledger-style models for Payment Certificate line items.

These models track financial items that work like bank accounts with
running balances throughout the project lifecycle. They include:
- Advance Payments
- Retention
- Materials on Site
- Escalation
- Special Items (contract-specific)
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from app.Account.models import Account
from app.core.Utilities.models import BaseModel

if TYPE_CHECKING:
    from app.Project.models import Project


class BaseLedgerItem(BaseModel):
    """
    Abstract base model for ledger-style items.

    Provides common functionality for items that track running balances
    with debit/credit transactions.
    """

    class TransactionType(models.TextChoices):
        """Type of ledger transaction."""

        DEBIT = "DEBIT", "Debit (Add)"
        CREDIT = "CREDIT", "Credit (Subtract)"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="%(class)s_items",
        help_text="Project this item belongs to",
    )
    payment_certificate = models.ForeignKey(
        "BillOfQuantities.PaymentCertificate",
        on_delete=models.CASCADE,
        related_name="%(class)s_transactions",
        help_text="Payment certificate this transaction is linked to",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        default=TransactionType.DEBIT,
        help_text="Whether this adds to or subtracts from the balance",
    )
    amount: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        help_text="Transaction amount (always positive)",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of the transaction",
    )
    date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of the transaction",
    )
    captured_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="captured_%(class)s_transactions",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes",
    )

    class Meta:
        abstract = True
        ordering = ["payment_certificate__certificate_number", "created_at"]

    def __str__(self) -> str:
        sign = "+" if self.transaction_type == self.TransactionType.DEBIT else "-"
        return f"{sign}{self.amount} ({self.description or 'No description'})"

    @property
    def signed_amount(self) -> Decimal:
        """Return amount with sign based on transaction type."""
        if self.transaction_type == self.TransactionType.CREDIT:
            return -self.amount
        return self.amount

    @classmethod
    def get_balance_for_project(cls, project: Project) -> Decimal:
        """Calculate current balance for a project."""
        transactions = cls.objects.filter(project=project)
        debit_total = transactions.filter(
            transaction_type=cls.TransactionType.DEBIT
        ).aggregate(
            total=Coalesce(
                Sum("amount"), Value(Decimal("0.00")), output_field=DecimalField()
            )
        )["total"]
        credit_total = transactions.filter(
            transaction_type=cls.TransactionType.CREDIT
        ).aggregate(
            total=Coalesce(
                Sum("amount"), Value(Decimal("0.00")), output_field=DecimalField()
            )
        )["total"]
        return debit_total - credit_total

    @classmethod
    def get_balance_up_to_certificate(
        cls, project: Project, certificate_number: int
    ) -> Decimal:
        """Calculate balance up to and including a specific certificate."""
        transactions = cls.objects.filter(
            project=project,
            payment_certificate__certificate_number__lte=certificate_number,
        )
        debit_total = transactions.filter(
            transaction_type=cls.TransactionType.DEBIT
        ).aggregate(
            total=Coalesce(
                Sum("amount"), Value(Decimal("0.00")), output_field=DecimalField()
            )
        )["total"]
        credit_total = transactions.filter(
            transaction_type=cls.TransactionType.CREDIT
        ).aggregate(
            total=Coalesce(
                Sum("amount"), Value(Decimal("0.00")), output_field=DecimalField()
            )
        )["total"]
        return debit_total - credit_total


class AdvancePayment(BaseLedgerItem):
    """
    Track advance payments made to the contractor.

    Advance payments are typically made at project start and recovered
    progressively through subsequent payment certificates.
    """

    class RecoveryMethod(models.TextChoices):
        """Method of advance payment recovery."""

        PERCENTAGE = "PERCENTAGE", "Percentage per Certificate"
        FIXED = "FIXED", "Fixed Amount per Certificate"
        MANUAL = "MANUAL", "Manual Recovery"

    # Original advance details (for DEBIT transactions)
    original_advance_amount: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original total advance amount (for reference)",
    )
    recovery_method = models.CharField(
        max_length=20,
        choices=RecoveryMethod.choices,
        default=RecoveryMethod.PERCENTAGE,
        help_text="How the advance will be recovered",
    )
    recovery_percentage: Decimal = models.DecimalField(  # type: ignore
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage to recover per certificate (if percentage method)",
    )

    # Guarantee/Security details
    guarantee_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Bank guarantee or security reference",
    )
    guarantee_expiry = models.DateField(
        null=True,
        blank=True,
        help_text="Expiry date of advance payment guarantee",
    )

    class Meta(BaseLedgerItem.Meta):
        verbose_name = "Advance Payment"
        verbose_name_plural = "Advance Payments"
        indexes = [
            models.Index(fields=["project", "payment_certificate"]),
        ]


class Retention(BaseLedgerItem):
    """
    Track retention amounts withheld and released.

    Retention is typically withheld from each payment certificate
    and released partially at practical completion and finally at
    final completion/end of defects liability period.
    """

    class RetentionType(models.TextChoices):
        """Type of retention transaction."""

        WITHHELD = "WITHHELD", "Retention Withheld"
        RELEASE_PRACTICAL = "RELEASE_PRACTICAL", "Release at Practical Completion"
        RELEASE_FINAL = "RELEASE_FINAL", "Release at Final Completion"
        RELEASE_PARTIAL = "RELEASE_PARTIAL", "Partial Release"

    retention_type = models.CharField(
        max_length=30,
        choices=RetentionType.choices,
        default=RetentionType.WITHHELD,
        help_text="Type of retention transaction",
    )
    retention_percentage: Decimal = models.DecimalField(  # type: ignore
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Retention percentage applied",
    )
    # Linked to work value for automatic calculation
    work_value_basis: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Work value this retention is calculated from",
    )
    release_certificate_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Certificate reference for retention release",
    )

    class Meta(BaseLedgerItem.Meta):
        verbose_name = "Retention"
        verbose_name_plural = "Retentions"
        indexes = [
            models.Index(fields=["project", "retention_type"]),
        ]


class MaterialsOnSite(BaseLedgerItem):
    """
    Track materials delivered to site but not yet incorporated.

    Materials on site are claimed when delivered and adjusted when
    incorporated into permanent works.
    """

    class MaterialStatus(models.TextChoices):
        """Status of materials on site."""

        CLAIMED = "CLAIMED", "Claimed"
        INCORPORATED = "INCORPORATED", "Incorporated into Works"
        REMOVED = "REMOVED", "Removed from Site"

    material_status = models.CharField(
        max_length=20,
        choices=MaterialStatus.choices,
        default=MaterialStatus.CLAIMED,
        help_text="Current status of the material",
    )
    material_description = models.CharField(
        max_length=500,
        help_text="Description of the material",
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Quantity of material",
    )
    unit = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Unit of measurement",
    )
    unit_price: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Unit price of material",
    )
    delivery_note_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Delivery note or invoice reference",
    )
    storage_location = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Location where material is stored on site",
    )

    class Meta(BaseLedgerItem.Meta):
        verbose_name = "Materials on Site"
        verbose_name_plural = "Materials on Site"
        indexes = [
            models.Index(fields=["project", "material_status"]),
        ]


class Escalation(BaseLedgerItem):
    """
    Track price escalation/adjustment claims.

    Escalation applies when contract allows for price adjustments
    based on indices or market conditions.
    """

    class EscalationType(models.TextChoices):
        """Type of escalation."""

        LABOUR = "LABOUR", "Labour Cost Escalation"
        MATERIAL = "MATERIAL", "Material Cost Escalation"
        FUEL = "FUEL", "Fuel Cost Escalation"
        COMBINED = "COMBINED", "Combined Escalation"
        INDEX_BASED = "INDEX_BASED", "Index-Based Escalation"

    escalation_type = models.CharField(
        max_length=20,
        choices=EscalationType.choices,
        default=EscalationType.COMBINED,
        help_text="Type of escalation",
    )
    base_date = models.DateField(
        null=True,
        blank=True,
        help_text="Base date for escalation calculation",
    )
    current_date = models.DateField(
        null=True,
        blank=True,
        help_text="Current/calculation date for escalation",
    )
    base_index: Decimal = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Base index value",
    )
    current_index: Decimal = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Current index value",
    )
    escalation_factor: Decimal = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Calculated escalation factor",
    )
    work_value_basis: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Work value escalation is applied to",
    )
    formula_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Reference to contract escalation formula",
    )

    class Meta(BaseLedgerItem.Meta):
        verbose_name = "Escalation"
        verbose_name_plural = "Escalations"
        indexes = [
            models.Index(fields=["project", "escalation_type"]),
        ]


class SpecialItemTransaction(BaseLedgerItem):
    """
    Track special/provisional items specific to the contract.

    These are contract-specific items that don't fit standard categories
    like dayworks, prime cost sums, provisional sums, etc.
    """

    class SpecialItemType(models.TextChoices):
        """Types of special items."""

        DAYWORK = "DAYWORK", "Daywork"
        PRIME_COST = "PRIME_COST", "Prime Cost Sum"
        PROVISIONAL = "PROVISIONAL", "Provisional Sum"
        CONTINGENCY = "CONTINGENCY", "Contingency"
        PENALTY = "PENALTY", "Penalty/Liquidated Damages"
        BONUS = "BONUS", "Bonus/Incentive"
        INSURANCE = "INSURANCE", "Insurance"
        OTHER = "OTHER", "Other"

    special_item_type = models.CharField(
        max_length=20,
        choices=SpecialItemType.choices,
        default=SpecialItemType.OTHER,
        help_text="Type of special item",
    )
    item_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Reference to contract clause or BOQ item",
    )
    budget_amount: Decimal = models.DecimalField(  # type: ignore
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original budget/provisional amount",
    )

    class Meta(BaseLedgerItem.Meta):
        verbose_name = "Special Item Transaction"
        verbose_name_plural = "Special Item Transactions"
        indexes = [
            models.Index(fields=["project", "special_item_type"]),
        ]
