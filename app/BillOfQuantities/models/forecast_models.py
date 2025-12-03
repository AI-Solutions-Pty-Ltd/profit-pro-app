from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet

from app.Account.models import Account
from app.core.Utilities.models import BaseModel, sum_queryset

if TYPE_CHECKING:
    from .structure_models import LineItem


class Forecast(BaseModel):
    """Capture forecasted work completed against a line item"""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"

    project = models.ForeignKey(
        "Project.Project", on_delete=models.CASCADE, related_name="forecasts"
    )
    period = models.DateField()
    status: Status = models.CharField(  # type: ignore
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    approved_by: Account = models.ForeignKey(  # type: ignore
        Account,
        on_delete=models.SET_NULL,
        related_name="approved_forecasts",
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)

    captured_by: Account = models.ForeignKey(  # type: ignore
        Account,
        on_delete=models.SET_NULL,
        related_name="captured_forecasts",
        blank=True,
        null=True,
    )

    if TYPE_CHECKING:
        forecast_transactions: QuerySet["ForecastTransaction"]

    class Meta:
        verbose_name = "Forecast"
        verbose_name_plural = "Forecasts"
        ordering = ["-period"]
        unique_together = [["project", "period"]]
        indexes = [
            models.Index(fields=["project", "period"]),
            models.Index(fields=["period"]),
        ]

    def __str__(self) -> str:
        return f"{self.period} - {self.status}"

    def clean(self) -> None:
        """Normalize period to first day of month (mm-yyyy format)."""
        if self.period:
            self.period = self.period.replace(day=1)

    def save(self, *args, **kwargs) -> None:
        self.clean()
        return super().save(*args, **kwargs)

    @property
    def total_forecast(self) -> Decimal:
        # return total of forecast transactions
        return sum_queryset(self.forecast_transactions, "total_price")


class ForecastTransaction(BaseModel):
    """Capture forecasted work completed against a line item"""

    class Type(models.TextChoices):
        PAYMENT_CERTIFICATE = "PAYMENT_CERTIFICATE", "Payment Certificate"
        FORECAST = "FORECAST", "Forecast"

    forecast: Forecast = models.ForeignKey(  # type: ignore
        Forecast,
        on_delete=models.CASCADE,
        related_name="forecast_transactions",
        blank=True,
        null=True,
    )
    line_item: "LineItem" = models.ForeignKey(  # type: ignore
        "BillOfQuantities.LineItem",
        on_delete=models.CASCADE,
        related_name="forecast_transactions",
        blank=True,
        null=True,
    )

    quantity: Decimal = models.DecimalField(max_digits=10, decimal_places=2)  # type: ignore
    unit_price: Decimal = models.DecimalField(  # type: ignore
        max_digits=10, decimal_places=2, blank=True
    )
    total_price: Decimal = models.DecimalField(  # type: ignore
        max_digits=10, decimal_places=2, blank=True
    )
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.line_item.description if self.line_item else self.line_item.pk} - {self.quantity}"
