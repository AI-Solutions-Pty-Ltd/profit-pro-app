from django.core.exceptions import ValidationError
from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.projects.projects_models import Project


class ProfitabilityBaseline(BaseModel):
    """
    Project-specific financial assumptions for targeted profitability.
    These define the 'Baseline' against which actual and forecast data are measured.
    """

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="profitability_baseline",
        help_text="Project these baseline assumptions belong to",
    )
    cost_of_sales_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=60.0,
        help_text="Targeted Cost of Sales as a percentage of revenue",
    )
    operating_expenses_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=12.0,
        help_text="Targeted Operating Expenses as a percentage of revenue",
    )
    net_profit_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=28.0,
        help_text="Targeted Net Profit as a percentage of revenue",
    )

    def clean(self):
        """Ensure percentages sum to 100%."""
        total = (
            self.cost_of_sales_percent
            + self.operating_expenses_percent
            + self.net_profit_percent
        )
        if total != 100:
            raise ValidationError(
                f"Percentages must sum to 100%. Current total: {total}%"
            )

    def __str__(self):
        return f"Baseline for {self.project.name}"

    class Meta:
        verbose_name = "Profitability Baseline"
        verbose_name_plural = "Profitability Baselines"
