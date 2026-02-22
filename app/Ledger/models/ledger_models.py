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


class FinancialStatement(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Financial Statement"
        verbose_name_plural = "Financial Statements"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ledger(BaseModel):
    """Ledger accounts"""

    company = models.ForeignKey("Project.Company", on_delete=models.CASCADE)
    financial_statement = models.ForeignKey(
        "FinancialStatement", on_delete=models.PROTECT, related_name="ledgers"
    )
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Ledger"
        verbose_name_plural = "Ledgers"
        ordering = ["financial_statement__name", "code", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"],
                name="unique_ledger_code",
            ),
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_ledger_name",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Transaction(BaseModel):
    """Transaction"""

    company = models.ForeignKey("Project.Company", on_delete=models.CASCADE)
    debit_ledger = models.ForeignKey(
        Ledger, on_delete=models.SET_NULL, null=True, related_name="debit_transactions"
    )
    credit_ledger = models.ForeignKey(
        Ledger, on_delete=models.SET_NULL, null=True, related_name="credit_transactions"
    )
    project = models.ForeignKey("Project.Project", on_delete=models.SET_NULL, null=True)
    structure = models.ForeignKey(
        "BillOfQuantities.Structure", on_delete=models.SET_NULL, null=True
    )
    bill = models.ForeignKey(
        "BillOfQuantities.Bill", on_delete=models.SET_NULL, null=True
    )
    date = models.DateField()
    amount_excl_vat = models.DecimalField(max_digits=10, decimal_places=2)
    amount_incl_vat = models.DecimalField(max_digits=10, decimal_places=2)
    vat = models.BooleanField(default=False)
    vat_rate = models.ForeignKey(Vat, on_delete=models.SET_NULL, null=True)
