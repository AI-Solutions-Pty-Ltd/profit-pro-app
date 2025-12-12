"""Views for Project app."""

import json
from datetime import datetime, timedelta
from typing import cast

from django.db.models import QuerySet
from django.http import JsonResponse
from django.views.generic import (
    ListView,
)

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import FilterForm
from app.Project.models import Portfolio, Project
from app.Project.models.compliance_models import ContractualCompliance


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
        self.filter_form = FilterForm(request.GET or {}, user=request.user)

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
        category = self.filter_form.cleaned_data.get("category")
        status = self.filter_form.cleaned_data.get("status")

        if search:
            projects = projects.filter(name__icontains=search)

        if category:
            projects = projects.filter(category=category)

        selected_project = self.filter_form.cleaned_data.get("projects")
        if selected_project:
            projects = projects.filter(pk=selected_project.pk)

        consultant = self.filter_form.cleaned_data.get("consultant")
        if consultant:
            projects = projects.filter(lead_consultant=consultant)

        if status and status != "ALL":
            projects = projects.filter(status=status)
        elif active_only:
            # Legacy support for active_only toggle
            projects = projects.filter(status=Project.Status.ACTIVE)

        return projects

    def get_context_data(self: "PortfolioDashboardView", **kwargs):
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)
        user: Account = self.request.user  # type: ignore
        projects: QuerySet[Project] = cast(QuerySet[Project], context["projects"])
        current_date = datetime.now()

        # Add the already-validated form to context
        context["filter_form"] = self.filter_form

        dashboard_data = []
        for project in projects:
            # Get contract value
            contract_value = project.total_contract_value

            # Get cumulative certified to date (sum of all approved payment certificates)
            certified_amount = project.get_actual_cost()

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
                project_cpi = project.get_cost_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                project_cpi = None
            try:
                project_spi = project.get_schedule_performance_index(current_date)
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
        # If no portfolio, return early with default values
        if not user.portfolio:  # type: ignore
            new_portfolio: Portfolio = Portfolio.objects.create()  #
            new_portfolio.users.add(user)  # type: ignore
            projects.update(portfolio=new_portfolio)
        user.refresh_from_db()
        portfolio: Portfolio = cast(Portfolio, user.portfolio)
        context["portfolio"] = portfolio
        context["current_date"] = current_date

        # Get category filter for portfolio-level calculations
        category_filter = (
            self.filter_form.cleaned_data.get("category")
            if self.filter_form and self.filter_form.is_valid()
            else None
        )

        # ==========================================
        # Group 1 - Project Stats
        # ==========================================
        active_count = portfolio.get_active_projects(category_filter).count()
        urgent_projects = portfolio.get_projects_requiring_urgent_intervention(
            current_date, category_filter
        )
        attention_projects = portfolio.get_projects_requiring_attention(
            current_date, category_filter
        )

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
        # Compliance Stats
        # ==========================================
        active_projects = portfolio.get_active_projects(category_filter)
        total_compliance_items = ContractualCompliance.objects.filter(
            project__in=active_projects
        ).count()
        completed_compliance_items = ContractualCompliance.objects.filter(
            project__in=active_projects,
            status=ContractualCompliance.Status.COMPLETED,
        ).count()
        overdue_compliance_items = ContractualCompliance.objects.filter(
            project__in=active_projects,
            status=ContractualCompliance.Status.OVERDUE,
        ).count()

        context["compliance_percentage"] = (
            round((completed_compliance_items / total_compliance_items * 100), 1)
            if total_compliance_items > 0
            else 0
        )
        context["urgent_compliance_count"] = overdue_compliance_items
        context["total_compliance_items"] = total_compliance_items

        # ==========================================
        # Group 2 - Budgets and Payments
        # ==========================================
        original_budget = portfolio.get_total_original_budget(category_filter)
        approved_variations = portfolio.get_total_approved_variations(category_filter)
        total_certified = portfolio.get_total_certified_value(category_filter)

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
        forecast_at_completion = portfolio.get_forecast_cost_at_completion(
            current_date, category_filter
        )
        cost_variance_at_completion = portfolio.get_cost_variance_at_completion(
            current_date, category_filter
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
        context["total_earned_value"] = portfolio.get_total_earned_value(
            current_date, category_filter
        )
        context["total_cost_variance"] = portfolio.get_total_cost_variance(
            current_date, category_filter
        )
        context["total_schedule_variance"] = portfolio.get_total_schedule_variance(
            current_date, category_filter
        )
        context["total_eac"] = portfolio.get_total_estimate_at_completion(
            current_date, category_filter
        )

        # Generate 6 months of CPI/SPI data for charts
        performance_data = self._get_performance_chart_data(
            portfolio, months=6, category=category_filter
        )
        context["performance_labels"] = json.dumps(performance_data["labels"])
        context["cpi_data"] = json.dumps(performance_data["cpi"])
        context["spi_data"] = json.dumps(performance_data["spi"])
        context["current_cpi"] = performance_data["current_cpi"]
        context["current_spi"] = performance_data["current_spi"]

        # Generate 12 months of Planned vs Actual vs Forecast vs Budget data
        cashflow_data = self._get_cashflow_chart_data(
            portfolio, category=category_filter
        )
        context["cashflow_labels"] = json.dumps(cashflow_data["labels"])
        context["planned_data"] = json.dumps(cashflow_data["planned"])
        context["actual_data"] = json.dumps(cashflow_data["actual"])
        context["forecast_data"] = json.dumps(cashflow_data["forecast"])
        context["budget_data"] = json.dumps(cashflow_data["budget"])
        context["cashflow_table_data"] = cashflow_data["table_data"]

        return context

    def _get_performance_chart_data(
        self: "PortfolioDashboardView",
        portfolio: Portfolio,
        months: int = 12,
        category=None,
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
                cpi = portfolio.get_cost_performance_index(month_date, category)
                cpi_values.append(float(cpi) if cpi else None)
            except (ZeroDivisionError, TypeError, Exception):
                cpi_values.append(None)

            try:
                spi = portfolio.get_schedule_performance_index(month_date, category)
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
        self: "PortfolioDashboardView", portfolio: Portfolio, category=None
    ) -> dict:
        """Generate 12 months of Planned vs Actual vs Forecast vs Budget data."""
        from decimal import Decimal

        labels = []
        planned_values = []
        actual_values = []
        forecast_values = []
        budget_values = []
        table_data = []

        current_date = datetime.now()
        # Monthly budget = total budget / 12 (simplified distribution)
        total_budget = portfolio.get_total_original_budget(category)
        monthly_budget = float(total_budget / 12) if total_budget else 0

        # Running cumulative totals
        cumulative_planned = Decimal("0.00")
        cumulative_forecast = Decimal("0.00")

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

            for project in portfolio.get_active_projects(category):
                try:
                    pv = project.get_planned_value(month_date)
                    if pv:
                        planned_total += pv
                except (ZeroDivisionError, TypeError, Exception):
                    pass

                try:
                    ac = project.get_actual_cost(month_date)
                    if ac:
                        actual_total += ac
                except (ZeroDivisionError, TypeError, Exception):
                    pass

                try:
                    fc = project.get_forecast_cost(month_date)
                    if fc:
                        forecast_total += fc
                except (ZeroDivisionError, TypeError, Exception):
                    pass

            planned_values.append(float(planned_total))
            actual_values.append(float(actual_total))
            forecast_values.append(float(forecast_total))

            # Update cumulative values
            cumulative_planned += planned_total
            cumulative_forecast += forecast_total

            # Calculate variance and percentages
            variance = cumulative_planned - cumulative_forecast
            variance_pct = (
                float((variance / cumulative_planned) * 100)
                if cumulative_planned > 0
                else 0
            )
            work_completed_pct = (
                float((cumulative_forecast / total_budget) * 100)
                if total_budget > 0
                else 0
            )

            table_data.append(
                {
                    "month": month_date.strftime("%b %Y"),
                    "cumulative_planned": float(cumulative_planned),
                    "cumulative_forecast": float(cumulative_forecast),
                    "variance": float(variance),
                    "variance_pct": round(variance_pct, 1),
                    "work_completed_pct": round(work_completed_pct, 1),
                }
            )

        return {
            "labels": labels,
            "planned": planned_values,
            "actual": actual_values,
            "forecast": forecast_values,
            "budget": budget_values,
            "table_data": table_data,
        }


class ProjectListView(PortfolioDashboardView):
    """Project list view that reuses dashboard filtering logic."""

    template_name = "portfolio/project_list.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
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

    def get(self: "ProjectListView", request, *args, **kwargs):
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
