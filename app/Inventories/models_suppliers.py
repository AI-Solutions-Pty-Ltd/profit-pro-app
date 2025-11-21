from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet


def supplier_invoice_upload_path(instance, filename):
    """Generate upload path for supplier invoice files."""
    return f"supplier_invoices/{instance.id}/{filename}"


class Supplier(models.Model):
    description = models.CharField(max_length=65, blank=False, null=False)
    company_registration = models.CharField(max_length=65, blank=False, null=False)
    vat = models.BooleanField(default=True)
    vat_number = models.BigIntegerField(blank=True, null=True)
    primary_contact = models.BigIntegerField(blank=False, null=False)
    email = models.CharField(max_length=100, blank=False, null=False)
    active = models.BooleanField(default=True)
    address = models.CharField(max_length=256, blank=True)

    if TYPE_CHECKING:
        transactions: QuerySet["Transaction"]

    def __str__(self):
        return self.description

    def get_transactions(self) -> QuerySet["Transaction"]:
        return self.transactions.all()


class Transaction(models.Model):
    class Category(models.TextChoices):
        INVOICE = "Invoice", "Invoice"
        CREDIT_NOTE = "Credit Note", "Credit Note"
        DEBIT_NOTE = "Debit Note", "Debit Note"

    date = models.DateTimeField(blank=False, null=False)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="transactions",
    )
    description = models.CharField(blank=False, null=False, max_length=100)
    category = models.CharField(
        choices=Category.choices,
        default=Category.INVOICE,
        max_length=20,
        blank=True,
    )
    amount_excl = models.DecimalField(
        blank=False, null=False, decimal_places=3, max_digits=10
    )
    amount_incl = models.DecimalField(
        blank=False, null=False, decimal_places=3, max_digits=10
    )

    def __str__(self):
        return f"{self.supplier} - {self.date}"


class Invoice(models.Model):
    date = models.DateTimeField()
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, blank=True, null=True
    )
    order = models.ForeignKey(
        "Inventories.order", on_delete=models.SET_NULL, blank=True, null=True
    )
    tx = models.ManyToManyField(Transaction)
    invoice = models.FileField(
        upload_to=supplier_invoice_upload_path,
        blank=True,
        null=True,
    )

    def __str__(self: "Invoice") -> str:
        return f"{self.supplier} - {self.date}"


class Bank(models.Model):
    bank = models.CharField(max_length=100)
    branch = models.CharField(max_length=6)

    def __str__(self):
        return self.bank


class BankingDetail(models.Model):
    supplier = models.OneToOneField(Supplier, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, on_delete=models.SET_NULL, blank=True, null=True)
    account = models.CharField(max_length=25)
    account_holder = models.CharField(max_length=100)

    def __str__(self):
        return self.bank
