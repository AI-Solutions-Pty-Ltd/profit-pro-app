"""Views for Project app."""

import json
from datetime import datetime, timedelta

from django.db.models import QuerySet
from django.http import JsonResponse
from django.views.generic import (
    ListView,
)

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import FilterForm
from app.Project.models import Portfolio, Project


class PortfolioDashboardView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Projects dashboard showing financial metrics for Portfolio."""

    model = Project
    template_name = "portfolio/portfolio_dashboard.html"
    context_object_name = "projects"
    permissions = ["consultant", "contractor"]

    filter_form: FilterForm | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_form = None

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        self.filter_form = FilterForm(request.GET or {})  # Ensure form is never None

    def get_breadcrumbs(self: "PortfolioDashboardView") -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": None},
            {"title": "Dashboard", "url": None},
        ]

    def get_queryset(self: "PortfolioDashboardView") -> QuerySet[Project]:
        """Get filtered projects for dashboard view."""
        # Ensure filter_form exists and is valid
        if not self.filter_form or not self.filter_form.is_valid():
            # Return unfiltered queryset if form is invalid
            return Project.objects.filter(account=self.request.user).order_by(
                "-created_at"
            )

        projects = Project.objects.filter(account=self.request.user).order_by(
            "-created_at"
        )

        # Apply filters from form
        search = self.filter_form.cleaned_data.get("search")
        active_only = self.filter_form.cleaned_data.get("active_projects")

        if search:
            projects = projects.filter(name__icontains=search)

        if active_only:
            projects = projects.filter(status=Project.Status.ACTIVE)

        return projects

    def get_context_data(self: "PortfolioDashboardView", **kwargs):
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)
        projects: QuerySet[Project] = context["projects"]
        current_date = datetime.now()

        # Add the already-validated form to context
        context["filter_form"] = self.filter_form

        dashboard_data = []
        for project in projects:
            # Get contract value
            contract_value = project.get_total_contract_value

            # Get cumulative certified to date (sum of all approved payment certificates)
            certified_amount = project.actual_cost()

            # Get latest forecast to date
            latest_forecast = project.forecasts.order_by("-period").first()
            forecast_amount = 0
            if latest_forecast:
                forecast_amount = latest_forecast.total_forecast

            # Calculate percentages
            certified_percentage = 0
            forecast_percentage = 0
            if contract_value > 0:
                certified_percentage = (certified_amount / contract_value) * 100
                forecast_percentage = (forecast_amount / contract_value) * 100

            # Get CPI and SPI for this project
            try:
                project_cpi = project.cost_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                project_cpi = None
            try:
                project_spi = project.schedule_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                project_spi = None

            dashboard_data.append(
                {
                    "project": project,
                    "contract_value": contract_value,
                    "certified_amount": certified_amount,
                    "forecast_amount": forecast_amount,
                    "certified_percentage": certified_percentage,
                    "forecast_percentage": forecast_percentage,
                    "cpi": project_cpi,
                    "spi": project_spi,
                }
            )

        context["total_contract_value"] = sum_queryset(
            projects, "line_items__total_price"
        )
        context["total_certified_amount"] = sum_queryset(
            projects, "payment_certificates__actual_transactions__total_price"
        )
        context["total_forecast_amount"] = sum_queryset(
            projects, "forecasts__forecast_transactions__total_price"
        )
        context["dashboard_data"] = dashboard_data
        portfolio: Portfolio = self.request.user.portfolio  # type: ignore
        context["portfolio"] = portfolio
        context["current_date"] = current_date

        # ==========================================
        # Group 1 - Project Stats
        # ==========================================
        active_count = portfolio.active_projects.count()
        urgent_projects = portfolio.projects_requiring_urgent_intervention(current_date)
        attention_projects = portfolio.projects_requiring_attention(current_date)

        context["active_projects_count"] = active_count
        context["urgent_projects"] = urgent_projects
        context["urgent_projects_count"] = len(urgent_projects)
        context["urgent_projects_percentage"] = (
            (len(urgent_projects) / active_count * 100) if active_count > 0 else 0
        )
        context["attention_projects"] = attention_projects
        context["attention_projects_count"] = len(attention_projects)
        context["attention_projects_percentage"] = (
            (len(attention_projects) / active_count * 100) if active_count > 0 else 0
        )

        # ==========================================
        # Group 2 - Budgets and Payments
        # ==========================================
        original_budget = portfolio.total_original_budget
        approved_variations = portfolio.total_approved_variations
        total_certified = portfolio.total_certified_value

        context["original_budget"] = original_budget
        context["approved_variations"] = approved_variations
        context["approved_variations_percentage"] = (
            (approved_variations / original_budget * 100) if original_budget > 0 else 0
        )
        context["total_certified"] = total_certified
        context["total_certified_percentage"] = (
            (total_certified / original_budget * 100) if original_budget > 0 else 0
        )

        # ==========================================
        # Cost Forecasts
        # ==========================================
        forecast_at_completion = portfolio.forecast_cost_at_completion(current_date)
        cost_variance_at_completion = portfolio.cost_variance_at_completion(
            current_date
        )

        context["forecast_at_completion"] = forecast_at_completion
        context["cost_variance_at_completion"] = cost_variance_at_completion
        context["cost_variance_at_completion_percentage"] = (
            (cost_variance_at_completion / original_budget * 100)
            if original_budget > 0 and cost_variance_at_completion
            else 0
        )

        # ==========================================
        # Earned Value Management (EVM)
        # ==========================================
        context["total_earned_value"] = portfolio.total_earned_value(current_date)
        context["total_cost_variance"] = portfolio.total_cost_variance(current_date)
        context["total_schedule_variance"] = portfolio.total_schedule_variance(
            current_date
        )
        context["total_eac"] = portfolio.total_estimate_at_completion(current_date)

        # Generate 6 months of CPI/SPI data for charts
        performance_data = self._get_performance_chart_data(portfolio, months=6)
        context["performance_labels"] = json.dumps(performance_data["labels"])
        context["cpi_data"] = json.dumps(performance_data["cpi"])
        context["spi_data"] = json.dumps(performance_data["spi"])
        context["current_cpi"] = performance_data["current_cpi"]
        context["current_spi"] = performance_data["current_spi"]

        # Generate 12 months of Planned vs Actual vs Forecast vs Budget data
        cashflow_data = self._get_cashflow_chart_data(portfolio)
        context["cashflow_labels"] = json.dumps(cashflow_data["labels"])
        context["planned_data"] = json.dumps(cashflow_data["planned"])
        context["actual_data"] = json.dumps(cashflow_data["actual"])
        context["forecast_data"] = json.dumps(cashflow_data["forecast"])
        context["budget_data"] = json.dumps(cashflow_data["budget"])

        return context

    def _get_performance_chart_data(
        self: "PortfolioDashboardView", portfolio: Portfolio, months: int = 12
    ) -> dict:
        """Generate N months of CPI/SPI data for portfolio."""
        labels = []
        cpi_values = []
        spi_values = []

        current_date = datetime.now()

        # Generate data for last N months (oldest to newest)
        for i in range(months - 1, -1, -1):
            # Calculate the date for this month
            month_date = current_date - timedelta(days=i * 30)
            # Normalize to first of month
            month_date = month_date.replace(day=1)

            labels.append(month_date.strftime("%b %Y"))

            try:
                cpi = portfolio.cost_performance_index(month_date)
                cpi_values.append(float(cpi) if cpi else None)
            except (ZeroDivisionError, TypeError, Exception):
                cpi_values.append(None)

            try:
                spi = portfolio.schedule_performance_index(month_date)
                spi_values.append(float(spi) if spi else None)
            except (ZeroDivisionError, TypeError, Exception):
                spi_values.append(None)

        return {
            "labels": labels,
            "cpi": cpi_values,
            "spi": spi_values,
            "current_cpi": cpi_values[-1] if cpi_values else None,
            "current_spi": spi_values[-1] if spi_values else None,
        }

    def _get_cashflow_chart_data(
        self: "PortfolioDashboardView", portfolio: Portfolio
    ) -> dict:
        """Generate 12 months of Planned vs Actual vs Forecast vs Budget data."""
        from decimal import Decimal

        labels = []
        planned_values = []
        actual_values = []
        forecast_values = []
        budget_values = []

        current_date = datetime.now()
        # Monthly budget = total budget / 12 (simplified distribution)
        monthly_budget = float(portfolio.total_original_budget / 12)

        # Generate data for last 12 months (oldest to newest)
        for i in range(11, -1, -1):
            # Calculate the date for this month
            month_date = current_date - timedelta(days=i * 30)
            # Normalize to first of month
            month_date = month_date.replace(day=1)

            labels.append(month_date.strftime("%b %Y"))
            budget_values.append(monthly_budget)

            # Aggregate planned, actual, and forecast for all projects
            planned_total = Decimal("0.00")
            actual_total = Decimal("0.00")
            forecast_total = Decimal("0.00")

            for project in portfolio.active_projects:
                try:
                    pv = project.planned_value(month_date)
                    if pv:
                        planned_total += pv
                except (ZeroDivisionError, TypeError, Exception):
                    pass

                try:
                    ac = project.actual_cost(month_date)
                    if ac:
                        actual_total += ac
                except (ZeroDivisionError, TypeError, Exception):
                    pass

                try:
                    fc = project.forecast_cost(month_date)
                    if fc:
                        forecast_total += fc
                except (ZeroDivisionError, TypeError, Exception):
                    pass

            planned_values.append(float(planned_total))
            actual_values.append(float(actual_total))
            forecast_values.append(float(forecast_total))

        return {
            "labels": labels,
            "planned": planned_values,
            "actual": actual_values,
            "forecast": forecast_values,
            "budget": budget_values,
        }


class ProjectListView(PortfolioDashboardView):
    """Project list view that reuses dashboard filtering logic."""

    template_name = "portfolio/project_list.html"

    def get_breadcrumbs(self):
        """Update breadcrumbs for project list page."""
        return [
            {"title": "Portfolio", "url": "/"},
            {"title": "Projects", "url": None},
        ]

    def get_context_data(self, **kwargs):
        """Simplify context data for project list view - no need for portfolio metrics."""
        context = super().get_context_data(**kwargs)

        # Remove portfolio-specific metrics that aren't needed for project list
        # Keep only the dashboard_data which contains project information
        portfolio_metrics_to_remove = [
            "total_contract_value",
            "total_certified_amount",
            "total_forecast_amount",
            "performance_labels",
            "cpi_data",
            "spi_data",
            "current_cpi",
            "current_spi",
        ]

        for metric in portfolio_metrics_to_remove:
            context.pop(metric, None)

        return context

    def get(self, request, *args, **kwargs):
        """Handle both regular GET and AJAX requests for filtering."""
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            # Return JSON response for AJAX requests
            self.object_list = self.get_queryset()
            context = self.get_context_data()

            # Render just the table body
            from django.template.loader import render_to_string

            html = render_to_string(
                "portfolio/_project_table_rows.html", context, request=request
            )

            return JsonResponse({"html": html})

        return super().get(request, *args, **kwargs)
