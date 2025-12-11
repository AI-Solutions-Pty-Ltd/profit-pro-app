from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

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
    def active_projects(self: "Portfolio") -> QuerySet[Project]:
        """Get all active projects in the portfolio."""
        return self.projects.filter(
            status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED]
        )

    def get_active_projects(
        self: "Portfolio", category: "ProjectCategory | None" = None
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

    # projects_requiring_urgent_intervention
    def get_projects_requiring_urgent_intervention(
        self: "Portfolio",
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> list[Project]:
        """Projects with CPI < 0.96 AND SPI < 0.96 (critical threshold)."""
        if not date:
            date = datetime.now()
        urgent = []
        for project in self.get_active_projects(category):
            try:
                cpi = project.get_cost_performance_index(date)
                spi = project.get_schedule_performance_index(date)
                # Both CPI and SPI must be below 0.96 for urgent intervention
                if (cpi and cpi < Decimal("0.96")) and (spi and spi < Decimal("0.96")):
                    urgent.append(project)
            except (ZeroDivisionError, TypeError):
                continue
        return urgent

    @property
    def projects_requiring_urgent_intervention(self: "Portfolio") -> list[Project]:
        return self.get_projects_requiring_urgent_intervention()

    # projects_requiring_attention
    def get_projects_requiring_attention(
        self: "Portfolio",
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> list[Project]:
        """Projects with CPI or SPI >= 0.96 but < 1.0 (not urgent)."""
        if not date:
            date = datetime.now()
        attention = []
        urgent_ids = [
            p.pk
            for p in self.get_projects_requiring_urgent_intervention(date, category)
        ]
        for project in self.get_active_projects(category):
            if project.pk in urgent_ids:
                continue
            try:
                cpi = project.get_cost_performance_index(date)
                spi = project.get_schedule_performance_index(date)
                # CPI or SPI is >= 0.96 but < 1.0
                cpi_needs_attention = cpi and Decimal("0.96") <= cpi < Decimal("1.0")
                spi_needs_attention = spi and Decimal("0.96") <= spi < Decimal("1.0")
                if cpi_needs_attention or spi_needs_attention:
                    attention.append(project)
            except (ZeroDivisionError, TypeError):
                continue
        return attention

    @property
    def projects_requiring_attention(self: "Portfolio") -> list[Project]:
        return self.get_projects_requiring_attention()

    # ==========================================
    # Group 2 - Budgets and Payments
    # ==========================================

    # total_original_budget
    def get_total_original_budget(
        self: "Portfolio", category: "ProjectCategory | None" = None
    ) -> Decimal:
        """Sum of original contract values with optional category filter."""
        projects = self.get_active_projects(category)
        if category:
            projects = projects.filter(category=category)

        # Filter at the LineItem level to ensure we only sum original items
        from app.BillOfQuantities.models.structure_models import LineItem

        line_items = LineItem.objects.filter(
            project__in=projects,
            addendum=False,
            special_item=False,
        )
        return sum_queryset(line_items, "total_price")

    @property
    def total_original_budget(self: "Portfolio") -> Decimal:
        """Sum of original contract values (excluding addendum/variations)."""
        return self.get_total_original_budget()

    # total_approved_variations
    def get_total_approved_variations(
        self: "Portfolio", category: Optional["ProjectCategory"] = None
    ) -> Decimal:
        """Sum of approved variations with optional category filter."""
        projects = self.get_active_projects(category)
        if category:
            projects = projects.filter(category=category)

        # Filter at the LineItem level to ensure we only sum addendum items
        from app.BillOfQuantities.models.structure_models import LineItem

        line_items = LineItem.objects.filter(
            project__in=projects,
            addendum=True,
            special_item=False,
        )
        return sum_queryset(line_items, "total_price")

    @property
    def total_approved_variations(self: "Portfolio") -> Decimal:
        """Sum of approved variations (addendum + special items)."""
        return self.get_total_approved_variations()

    # total_contract_value
    def get_total_contract_value(
        self: "Portfolio", category: Optional["ProjectCategory"] = None
    ) -> Decimal:
        """Total contract value with optional category filter."""
        projects = self.get_active_projects(category)
        if category:
            projects = projects.filter(category=category)

        # Filter at the LineItem level to ensure we only sum non-special items
        from app.BillOfQuantities.models.structure_models import LineItem

        line_items = LineItem.objects.filter(
            project__in=projects,
            special_item=False,
        )
        return sum_queryset(line_items, "total_price")

    @property
    def total_contract_value(self: "Portfolio") -> Decimal:
        """Total contract value including variations."""
        return self.get_total_contract_value()

    # total_forecast_value
    def get_total_forecast_value(
        self: "Portfolio", category: "ProjectCategory | None" = None
    ) -> Decimal:
        """Sum of latest forecast values with optional category filter."""
        return sum_queryset(self.get_active_projects(category), "forecasts")

    @property
    def total_forecast_value(self: "Portfolio") -> Decimal:
        """Sum of latest forecast values for all active projects."""
        return self.get_total_forecast_value()

    # total_certified_value
    def get_total_certified_value(
        self: "Portfolio", category: "ProjectCategory | None" = None
    ) -> Decimal:
        """Total certified amount with optional category filter."""
        return sum_queryset(
            self.get_active_projects(category),
            "payment_certificates__actual_transactions__total_price",
        )

    @property
    def total_certified_value(self: "Portfolio") -> Decimal:
        """Total certified amount to date."""
        return self.get_total_certified_value()

    # ==========================================
    # Cost Forecasts
    # ==========================================

    # forecast_cost_at_completion
    def get_forecast_cost_at_completion(
        self: "Portfolio",
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Sum of latest cost forecasts for all active projects."""
        if not date:
            date = datetime.now()
        total = Decimal("0.00")
        valid_count = 0
        for project in self.get_active_projects(category):
            try:
                # Use latest approved forecast instead of EAC
                latest_forecast = (
                    project.forecasts.filter(status=Forecast.Status.APPROVED)
                    .order_by("-period")
                    .first()
                )
                if latest_forecast:
                    forecast_total = latest_forecast.total_forecast or Decimal("0.00")
                    total += forecast_total
                    valid_count += 1
            except (ZeroDivisionError, TypeError):
                continue
        return total if valid_count > 0 else None

    @property
    def forecast_cost_at_completion(self: "Portfolio") -> Decimal | None:
        return self.get_forecast_cost_at_completion()

    # cost_variance_at_completion
    def get_cost_variance_at_completion(
        self: "Portfolio",
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Original Budget - Forecast Cost at Completion."""
        if not date:
            date = datetime.now()
        eac = self.get_forecast_cost_at_completion(date, category)
        if not eac:
            return None
        return self.get_total_original_budget(category) - eac

    @property
    def cost_variance_at_completion(self: "Portfolio") -> Decimal | None:
        return self.get_cost_variance_at_completion()

    # ==========================================
    # Earned Value Management (EVM)
    # ==========================================

    # total_earned_value
    def get_total_earned_value(
        self: "Portfolio",
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
                ev = project.get_earned_value(date)
                if ev:
                    total += ev
                    valid_count += 1
            except (ZeroDivisionError, TypeError):
                continue
        return total if valid_count > 0 else None

    @property
    def total_earned_value(self: "Portfolio") -> Decimal | None:
        return self.get_total_earned_value()

    # total_cost_variance
    def get_total_cost_variance(
        self: "Portfolio",
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
                cv = project.get_cost_variance(date)
                if cv:
                    total += cv
                    valid_count += 1
            except (ZeroDivisionError, TypeError):
                continue
        return total if valid_count > 0 else None

    @property
    def total_cost_variance(self: "Portfolio") -> Decimal | None:
        return self.get_total_cost_variance()

    # total_schedule_variance
    def get_total_schedule_variance(
        self: "Portfolio",
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
                sv = project.get_schedule_variance(date)
                if sv:
                    total += sv
                    valid_count += 1
            except (ZeroDivisionError, TypeError):
                continue
        return total if valid_count > 0 else None

    @property
    def total_schedule_variance(self: "Portfolio") -> Decimal | None:
        return self.get_total_schedule_variance()

    # total_estimate_at_completion
    def get_total_estimate_at_completion(
        self: "Portfolio",
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
    ) -> Decimal | None:
        """Sum of EAC for all active projects."""
        return self.get_forecast_cost_at_completion(date, category)

    @property
    def total_estimate_at_completion(self: "Portfolio") -> Decimal | None:
        return self.get_total_estimate_at_completion()

    # cost_performance_index
    def get_cost_performance_index(
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
                project_cpi = project.get_cost_performance_index(date)
                if project_cpi:
                    cpi += project_cpi
                    valid_projects += 1
            except (ZeroDivisionError, TypeError):
                print(f"Error calculating CPI for project {project.name}")
                continue
        if valid_projects == 0:
            return None
        return round(cpi / Decimal(valid_projects), 2)

    @property
    def cost_performance_index(self: "Portfolio") -> Decimal | None:
        return self.get_cost_performance_index()

    # schedule_performance_index
    def get_schedule_performance_index(
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
                project_spi = project.get_schedule_performance_index(date)
                if project_spi:
                    spi += project_spi
                    valid_projects += 1
            except (ZeroDivisionError, TypeError):
                continue
        if valid_projects == 0:
            return None
        return round(spi / Decimal(valid_projects), 2)

    @property
    def schedule_performance_index(self: "Portfolio") -> Decimal | None:
        return self.get_schedule_performance_index()
