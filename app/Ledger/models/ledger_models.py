from django.db import models

from app.core.Utilities.models import BaseModel

# Create your models here.


class Vat(BaseModel):
    """Global VAT configuration"""

    rate = models.DecimalField(max_digits=5, decimal_places=2)
    name = models.CharField(max_length=100)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    class Meta:
        verbose_name = "VAT"
        verbose_name_plural = "VATs"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} - {self.rate}%"


class Ledger(BaseModel):
    """Ledger accounts"""

    company = models.ForeignKey("Project.Company", on_delete=models.CASCADE)

    class FinancialStatement(models.TextChoices):
        BALANCE_SHEET = "balance_sheet", "Balance Sheet"
        INCOME_STATEMENT = "income_statement", "Income Statement"
        CASH_FLOW_STATEMENT = "cash_flow_statement", "Cash Flow Statement"
        STATEMENT_OF_CHANGES_IN_EQUITY = (
            "statement_of_changes_in_equity",
            "Statement of Changes in Equity",
        )

    financial_statement = models.CharField(
        max_length=35,
        choices=FinancialStatement.choices,
        default=FinancialStatement.BALANCE_SHEET,
    )
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Ledger"
        verbose_name_plural = "Ledgers"
        ordering = ["financial_statement", "code", "name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Transaction(BaseModel):
    """Transaction"""

    class TransactionType(models.TextChoices):
        DEBIT = "debit", "Debit"
        CREDIT = "credit", "Credit"

    company = models.ForeignKey("Project.Company", on_delete=models.CASCADE)
    ledger = models.ForeignKey(Ledger, on_delete=models.SET_NULL, null=True)
    bill = models.ForeignKey(
        "BillOfQuantities.Bill", on_delete=models.SET_NULL, null=True
    )
    date = models.DateField()
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount_excl_vat = models.DecimalField(max_digits=10, decimal_places=2)
    amount_incl_vat = models.DecimalField(max_digits=10, decimal_places=2)
    vat = models.BooleanField(default=False)
    vat_rate = models.ForeignKey(Vat, on_delete=models.SET_NULL, null=True)
