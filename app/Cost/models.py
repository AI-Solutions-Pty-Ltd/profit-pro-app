from django.db import models
from django.urls import reverse

from app.BillOfQuantities.models import Bill
from app.core.Utilities.models import BaseModel


# Create your models here.
class Cost(BaseModel):
    """Cost model representing costs associated with a bill."""

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="costs")
    date = models.DateField()
    description = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    vat = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Cost"
        verbose_name_plural = "Costs"

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse(
            "cost:bill-cost-detail",
            kwargs={"project_pk": self.bill.structure.project.pk, "bill_pk": self.bill.pk},
        )
