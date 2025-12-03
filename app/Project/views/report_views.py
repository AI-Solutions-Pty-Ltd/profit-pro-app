"""Views for Portfolio Reports."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from django.db.models import QuerySet, Sum
from django.urls import reverse
from django.views.generic import ListView

from app.BillOfQuantities.models import Forecast
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Project
from app.Project.models.projects_models import Portfolio


class FinancialReportView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Financial Report - Project List with Budget, Forecast, Variances, Certified, CPI & SPI."""

    model = Project
    template_name = "portfolio/reports/financial_report.html"
    context_object_name = "projects"
    permissions = ["consultant", "contractor"]

    def get_breadcrumbs(self: "FinancialReportView") -> list[BreadcrumbItem]:
        """Return breadcrumbs for financial report."""
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-list"),
            ),
            BreadcrumbItem(
                title="Reports",
                url=None,
            ),
            BreadcrumbItem(
                title="Financial Report",
                url=None,
            ),
        ]

    def get_queryset(self: "FinancialReportView") -> QuerySet[Project]:
        """Get active projects for the user's portfolio."""
        return Project.objects.filter(
            account=self.request.user,
            status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED],
        ).order_by("name")

    def get_context_data(self: "FinancialReportView", **kwargs: Any) -> dict[str, Any]:
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)
        projects: QuerySet[Project] = context["projects"]
        current_date = datetime.now()

        report_data = []
        totals = {
            "budget": Decimal("0.00"),
            "forecast": Decimal("0.00"),
            "variance": Decimal("0.00"),
            "certified": Decimal("0.00"),
        }

        for project in projects:
            # Budget (Original Contract Value)
            budget = project.get_original_contract_value or Decimal("0.00")

            # Forecast (Latest approved forecast total)
            latest_forecast = (
                project.forecasts.filter(status=Forecast.Status.APPROVED)
                .order_by("-period")
                .first()
            )
            forecast_total = Decimal("0.00")
            if latest_forecast:
                forecast_total = latest_forecast.forecast_transactions.aggregate(
                    total=Sum("total_price")
                )["total"] or Decimal("0.00")

            # Variance
            variance = forecast_total - budget

            # Certified (Actual cost to date)
            certified = project.actual_cost() or Decimal("0.00")

            # CPI & SPI
            try:
                cpi = project.cost_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                cpi = None

            try:
                spi = project.schedule_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                spi = None

            report_data.append(
                {
                    "project": project,
                    "budget": budget,
                    "forecast": forecast_total,
                    "variance": variance,
                    "variance_percentage": (variance / budget * 100)
                    if budget
                    else Decimal("0.00"),
                    "certified": certified,
                    "cpi": cpi,
                    "spi": spi,
                }
            )

            # Accumulate totals
            totals["budget"] += budget
            totals["forecast"] += forecast_total
            totals["variance"] += variance
            totals["certified"] += certified

        # Calculate total variance percentage
        totals["variance_percentage"] = (
            (totals["variance"] / totals["budget"] * 100)
            if totals["budget"]
            else Decimal("0.00")
        )

        context["report_data"] = report_data
        context["totals"] = totals
        context["current_date"] = current_date
        context["portfolio"]: Portfolio = self.request.user.portfolio  # type: ignore

        return context


class ScheduleReportView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Schedule Report - Project List with Planned Time, Forecast, Actual."""

    model = Project
    template_name = "portfolio/reports/schedule_report.html"
    context_object_name = "projects"
    permissions = ["consultant", "contractor"]

    def get_breadcrumbs(self: "ScheduleReportView") -> list[BreadcrumbItem]:
        """Return breadcrumbs for schedule report."""
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-list"),
            ),
            BreadcrumbItem(
                title="Reports",
                url=None,
            ),
            BreadcrumbItem(
                title="Schedule Report",
                url=None,
            ),
        ]

    def get_queryset(self: "ScheduleReportView") -> QuerySet[Project]:
        """Get active projects for the user's portfolio."""
        return Project.objects.filter(
            account=self.request.user,
            status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED],
        ).order_by("name")

    def get_context_data(self: "ScheduleReportView", **kwargs: Any) -> dict[str, Any]:
        """Add schedule metrics to context."""
        context = super().get_context_data(**kwargs)
        projects: QuerySet[Project] = context["projects"]
        current_date = datetime.now()

        report_data = []

        for project in projects:
            # Planned duration (days)
            planned_start = project.start_date
            planned_end = project.end_date
            planned_duration = None
            if planned_start and planned_end:
                planned_duration = (planned_end - planned_start).days

            # Forecast end date (from time forecast if available)
            forecast_end = project.end_date  # Default to planned end

            # Actual progress (days elapsed)
            days_elapsed = None
            if planned_start:
                days_elapsed = (current_date.date() - planned_start).days
                if days_elapsed < 0:
                    days_elapsed = 0

            # Percentage complete (based on certified vs budget)
            budget = project.get_original_contract_value or Decimal("0.00")
            certified = project.actual_cost() or Decimal("0.00")
            percent_complete = (certified / budget * 100) if budget else Decimal("0.00")

            # SPI
            try:
                spi = project.schedule_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                spi = None

            report_data.append(
                {
                    "project": project,
                    "planned_start": planned_start,
                    "planned_end": planned_end,
                    "planned_duration": planned_duration,
                    "forecast_end": forecast_end,
                    "days_elapsed": days_elapsed,
                    "percent_complete": percent_complete,
                    "spi": spi,
                }
            )

        context["report_data"] = report_data
        context["current_date"] = current_date
        context["portfolio"]: Portfolio = self.request.user.portfolio  # type: ignore

        return context
