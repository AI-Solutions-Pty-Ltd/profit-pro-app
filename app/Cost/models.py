from django.conf import settings
from django.db import models
from django.urls import reverse

from app.BillOfQuantities.models import Bill
from app.core.Utilities.models import BaseModel


# Create your models here.
class AbstractCost(BaseModel):
    """Cost model representing costs associated with a bill."""

    class Category(models.TextChoices):
        MATERIAL = "MATERIAL", "Material"
        LABOUR = "LABOUR", "Labour"
        EQUIPMENT = "EQUIPMENT", "Equipment"
        PLANT = "PLANT", "Plant"
        OTHER = "OTHER", "Other"

    date = models.DateField()
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    gross = models.DecimalField(max_digits=10, decimal_places=2)
    vat = models.BooleanField(default=True)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    net = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        abstract = True

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        self.gross = self.quantity * self.unit_price
        self.vat_amount = self.gross * settings.VAT_RATE if self.vat else 0
        self.net = self.gross + self.vat_amount
        super().save(*args, **kwargs)


class Cost(AbstractCost):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="costs")

    class Meta:
        verbose_name = "Cost"
        verbose_name_plural = "Costs"
        ordering = ["category", "-date", "description"]

    def get_absolute_url(self):
        return reverse(
            "cost:bill-cost-detail",
            kwargs={
                "project_pk": self.bill.structure.project.pk,
                "bill_pk": self.bill.pk,
            },
        )


class ActualCost(AbstractCost):
    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, related_name="actual_costs"
    )
    cost = models.ForeignKey(
        Cost, on_delete=models.CASCADE, related_name="actual_costs"
    )

    class Meta:
        verbose_name = "Actual Cost"
        verbose_name_plural = "Actual Costs"
        ordering = ["category", "-date", "description"]

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse(
            "cost:bill-cost-detail",
            kwargs={
                "project_pk": self.bill.structure.project.pk,
                "bill_pk": self.bill.pk,
            },
        )
