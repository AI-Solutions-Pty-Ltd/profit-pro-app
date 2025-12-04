from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet

from app.Account.models import Account
from app.BillOfQuantities.models.forecast_models import Forecast
from app.core.Utilities.models import BaseModel, sum_queryset
from app.Project.models.projects_models import Project

if TYPE_CHECKING:
    from app.Project.models.category_models import ProjectCategory


class Portfolio(BaseModel):
    """Portfolio model for grouping and aggregating project metrics."""

    users = models.ManyToManyField(Account, null=True, related_name="portfolios")

    def __str__(self) -> str:
        return super().__str__()

    if TYPE_CHECKING:
        projects: QuerySet[Project]

    # ==========================================
    # Group 1 - Project Stats
    # ==========================================

    @property
    def active_projects(self) -> QuerySet[Project]:
        """Get all active projects in the portfolio."""
        return self.projects.filter(
            status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED]
        )

    def get_active_projects(
        self, category: "ProjectCategory | None" = None
    ) -> QuerySet[Project]:
        """Get active projects with optional category filter.

        Args:
            category: Optional ProjectCategory to filter by.

        Returns:
            QuerySet of active projects, optionally filtered by category.
        """
        projects = self.active_projects
        if category:
            projects = projects.filter(category=category)
        return projects

    def projects_requiring_urgent_intervention(
        self, date: datetime | None = None, category: "ProjectCategory | None" = None
    ) -> list[Project]:
        """Projects with CPI < 0.9 or SPI < 0.9 (critical threshold)."""
        if not date:
            date = datetime.now()
        urgent = []
        for project in self.get_active_projects(category):
            try:
                cpi = project.cost_performance_index(date)
                spi = project.schedule_performance_index(date)
                if (cpi and cpi < Decimal("0.9")) or (spi and spi < Decimal("0.9")):
                    urgent.append(project)
            except (ZeroDivisionError, TypeError):
                continue
        return urgent

    def projects_requiring_attention(
        self, date: datetime | None = None, category: "ProjectCategory | None" = None
    ) -> list[Project]:
        """Projects with CPI < 1.0 or SPI < 1.0 (but not urgent)."""
        if not date:
            date = datetime.now()
        attention = []
        urgent_ids = [
            p.pk for p in self.projects_requiring_urgent_intervention(date, category)
        ]
        for project in self.get_active_projects(category):
            if project.pk in urgent_ids:
                continue
            try:
                cpi = project.cost_performance_index(date)
                spi = project.schedule_performance_index(date)
                if (cpi and cpi < Decimal("1.0")) or (spi and spi < Decimal("1.0")):
                    attention.append(project)
            except (ZeroDivisionError, TypeError):
                continue
        return attention

    # ==========================================
    # Group 2 - Budgets and Payments
    # ==========================================

    @property
    def total_original_budget(self) -> Decimal:
        """Sum of original contract values (excluding addendums/variations)."""
        return self.get_total_original_budget()

    def get_total_original_budget(
        self, category: "ProjectCategory | None" = None
    ) -> Decimal:
        """Sum of original contract values with optional category filter."""
        total = Decimal("0.00")
        for project in self.get_active_projects(category):
            total += project.get_original_contract_value or Decimal("0.00")
        return total

    @property
    def total_approved_variations(self) -> Decimal:
        """Sum of approved variations (addendum + special items)."""
        return self.get_total_approved_variations()

    def get_total_approved_variations(
        self, category: "ProjectCategory | None" = None
    ) -> Decimal:
        """Sum of approved variations with optional category filter."""
        total = Decimal("0.00")
        for project in self.get_active_projects(category):
            total += project.contract_addendum_value or Decimal("0.00")
        return total

    @property
    def total_contract_value(self) -> Decimal:
        """Total contract value including variations."""
        return sum_queryset(self.active_projects, "line_items__total_price")

    def get_total_contract_value(
        self, category: "ProjectCategory | None" = None
    ) -> Decimal:
        """Total contract value with optional category filter."""
        return sum_queryset(
            self.get_active_projects(category), "line_items__total_price"
        )

    @property
    def total_forecast_value(self) -> Decimal:
        """Sum of latest forecast values for all active projects."""
        return self.get_total_forecast_value()

    def get_total_forecast_value(
        self, category: "ProjectCategory | None" = None
    ) -> Decimal:
        """Sum of latest forecast values with optional category filter."""
        total_forecast_value = Decimal(0)
        for project in self.get_active_projects(category):
            last_forecast: Forecast | None = project.forecasts.order_by(
                "-period"
            ).last()
            if last_forecast:
                total_forecast_value += last_forecast.total_forecast
        return total_forecast_value

    @property
    def total_certified_value(self) -> Decimal:
        """Total certified amount to date."""
        return self.get_total_certified_value()

    def get_total_certified_value(
        self, category: "ProjectCategory | None" = None
    ) -> Decimal:
        """Total certified amount with optional category filter."""
        return sum_queryset(
            self.get_active_projects(category),
            "payment_certificates__actual_transactions__total_price",
        )

    # ==========================================
    # Cost Forecasts
    # ==========================================

    def forecast_cost_at_completion(
        self,
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Sum of EAC (Estimate at Completion) for all active projects."""
        if not date:
            date = datetime.now()
        total = Decimal("0.00")
        valid_count = 0
        for project in self.get_active_projects(category):
            try:
                eac = project.estimate_at_completion(date)
                if eac:
                    total += eac
                    valid_count += 1
            except (ZeroDivisionError, TypeError):
                continue
        return total if valid_count > 0 else None

    def cost_variance_at_completion(
        self,
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Original Budget - Forecast Cost at Completion."""
        if not date:
            date = datetime.now()
        eac = self.forecast_cost_at_completion(date, category)
        if not eac:
            return None
        return self.get_total_original_budget(category) - eac

    # ==========================================
    # Earned Value Management (EVM)
    # ==========================================

    def total_earned_value(
        self,
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Sum of earned value for all active projects."""
        if not date:
            date = datetime.now()
        total = Decimal("0.00")
        valid_count = 0
        for project in self.get_active_projects(category):
            try:
                ev = project.earned_value(date)
                if ev:
                    total += ev
                    valid_count += 1
            except (ZeroDivisionError, TypeError):
                continue
        return total if valid_count > 0 else None

    def total_cost_variance(
        self,
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Sum of cost variance for all active projects (EV - AC)."""
        if not date:
            date = datetime.now()
        total = Decimal("0.00")
        valid_count = 0
        for project in self.get_active_projects(category):
            try:
                cv = project.cost_variance(date)
                if cv:
                    total += cv
                    valid_count += 1
            except (ZeroDivisionError, TypeError):
                continue
        return total if valid_count > 0 else None

    def total_schedule_variance(
        self,
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Sum of schedule variance for all active projects (EV - PV)."""
        if not date:
            date = datetime.now()
        total = Decimal("0.00")
        valid_count = 0
        for project in self.get_active_projects(category):
            try:
                sv = project.schedule_variance(date)
                if sv:
                    total += sv
                    valid_count += 1
            except (ZeroDivisionError, TypeError):
                continue
        return total if valid_count > 0 else None

    def total_estimate_at_completion(
        self,
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Sum of EAC for all active projects."""
        return self.forecast_cost_at_completion(date, category)

    def cost_performance_index(
        self: "Portfolio",
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Portfolio-level CPI (average of all active projects)."""
        if not date:
            date = datetime.now()
        active_projects = self.get_active_projects(category)
        if active_projects.count() == 0:
            return None
        cpi = Decimal(0)
        valid_projects = 0
        for project in active_projects:
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
        self: "Portfolio",
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Portfolio-level SPI (average of all active projects)."""
        if not date:
            date = datetime.now()
        active_projects = self.get_active_projects(category)
        if active_projects.count() == 0:
            return None
        spi = Decimal(0)
        valid_projects = 0
        for project in active_projects:
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
