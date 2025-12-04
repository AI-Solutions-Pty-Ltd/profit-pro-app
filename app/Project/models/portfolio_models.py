from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet

from app.Account.models import Account
from app.BillOfQuantities.models.forecast_models import Forecast
from app.core.Utilities.models import BaseModel, sum_queryset
from app.Project.models.projects_models import Project


class Portfolio(BaseModel):
    users = models.ManyToManyField(Account, null=True, related_name="portfolios")

    def __str__(self) -> str:
        return super().__str__()

    if TYPE_CHECKING:
        projects: QuerySet[Project]

    @property
    def active_projects(self) -> QuerySet[Project]:
        return self.projects.filter(
            status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED]
        )

    @property
    def total_contract_value(self) -> Decimal:
        return sum_queryset(self.active_projects, "line_items__total_price")

    @property
    def total_forecast_value(self) -> Decimal:
        total_forecast_value = Decimal(0)
        for project in self.active_projects:
            last_forecast: Forecast | None = project.forecasts.order_by(
                "-period"
            ).last()
            if last_forecast:
                total_forecast_value += last_forecast.total_forecast
        return total_forecast_value

    @property
    def total_certified_value(self) -> Decimal:
        return sum_queryset(
            self.active_projects,
            "payment_certificates__actual_transactions__total_price",
        )

    def cost_performance_index(
        self: "Portfolio", date: datetime | None
    ) -> Decimal | None:
        """Portfolio-level CPI (average of all active projects)."""
        if not date:
            date = datetime.now()
        active_count = self.active_projects.count()
        if active_count == 0:
            return None
        cpi = Decimal(0)
        valid_projects = 0
        for project in self.active_projects:
            try:
                project_cpi = project.cost_performance_index(date)
                if project_cpi:
                    cpi += project_cpi
                    valid_projects += 1
            except (ZeroDivisionError, TypeError):
                print(f"Error calculating CPI for project {project.name}")
                continue
        if valid_projects == 0:
            return None
        return round(cpi / Decimal(valid_projects), 2)

    def schedule_performance_index(
        self: "Portfolio", date: datetime | None
    ) -> Decimal | None:
        """Portfolio-level SPI (average of all active projects)."""
        if not date:
            date = datetime.now()
        active_count = self.active_projects.count()
        if active_count == 0:
            return None
        spi = Decimal(0)
        valid_projects = 0
        for project in self.active_projects:
            try:
                project_spi = project.schedule_performance_index(date)
                if project_spi:
                    spi += project_spi
                    valid_projects += 1
            except (ZeroDivisionError, TypeError):
                continue
        if valid_projects == 0:
            return None
        return round(spi / Decimal(valid_projects), 2)
