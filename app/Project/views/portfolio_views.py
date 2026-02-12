"""Views for Project app - Portfolio Dashboard and Reports."""

import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.views.generic import (
    ListView,
    TemplateView,
)

from app.Account.models import Account
from app.core.Utilities.dates import get_previous_n_months
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import FilterForm
from app.Project.models import (
    AdministrativeCompliance,
    ContractualCompliance,
    FinalAccountCompliance,
    Portfolio,
    Project,
    ProjectImpact,
    Risk,
)


class CompanyDashboardView(LoginRequiredMixin, BreadcrumbMixin, ListView):
    """Projects dashboard showing financial metrics for Portfolio."""

    model = Project
    template_name = "portfolio/company_dashboard.html"
    context_object_name = "projects"

    filter_form: FilterForm | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_form = None

    def setup(self, request, *args, **kwargs):
        """Initialize view during setup."""
        super().setup(request, *args, **kwargs)

    def get_breadcrumbs(self: "CompanyDashboardView") -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": None},
            {"title": "Dashboard", "url": None},
        ]

    def get_queryset(self: "CompanyDashboardView") -> QuerySet[Project]:
        """Get filtered projects for dashboard view."""
        # Initialize filter form with user's projects
        user: Account = self.request.user  # type: ignore
        projects = user.get_projects.order_by("-created_at")

        # Initialize filter form with the base queryset
        self.filter_form = FilterForm(
            self.request.GET or {}, user=user, projects_queryset=projects
        )

        if not self.filter_form or not self.filter_form.is_valid():
            # Return unfiltered queryset if form is invalid
            return projects

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

    def get_context_data(self: "CompanyDashboardView", **kwargs):
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
        if not user.portfolio:
            new_portfolio: Portfolio = Portfolio.objects.create()  #
            new_portfolio.users.add(user)
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
        active_projects = portfolio.get_active_projects(category_filter)
        active_count = active_projects.count()
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
        # Group 2 - Income Statement
        # ==========================================
        # Income Statement Summary (dummy data for now)
        context["revenue"] = 15000000  # R15M
        context["variable_costs"] = 12000000  # R12M
        context["gross_profit"] = 3000000  # R3M
        context["gross_profit_margin"] = 20.0  # 20%
        context["net_profit"] = 1200000  # R1.2M
        context["net_profit_margin"] = 8.0  # 8%
        context["forecast_profit"] = 2500000  # R2.5M
        context["profits"] = 1200000  # R1.2M (same as net profit for Company Status)

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

        # Profit trend data for charts
        profit_data = self._get_profit_trend_data()
        context["profit_labels"] = json.dumps(profit_data["labels"])
        context["gross_profit_percentage_data"] = json.dumps(
            profit_data["gross_profit_percentages"]
        )
        context["net_profit_data"] = json.dumps(profit_data["net_profit_values"])

        return context

    def _get_performance_chart_data(
        self: "CompanyDashboardView",
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
        self: "CompanyDashboardView", portfolio: Portfolio, category=None
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

    def _get_profit_trend_data(self) -> dict:
        """Generate 6 months of profit trend data for charts.

        Returns:
            dict: Contains labels, gross_profit_percentages, and net_profit_values
        """
        labels = [month.strftime("%b %Y") for month in get_previous_n_months(6)]
        # Generate dummy gross profit percentages (10-30%)
        gross_profit_percentages = [round(random.uniform(10, 30), 1) for _ in range(6)]
        # Generate dummy net profit values (500k-1.5M)
        net_profit_values = [
            round(random.uniform(500000, 1500000), 0) for _ in range(6)
        ]

        return {
            "labels": labels,
            "gross_profit_percentages": gross_profit_percentages,
            "net_profit_values": net_profit_values,
        }


class PortfolioDashboardView(LoginRequiredMixin, BreadcrumbMixin, ListView):
    """Projects dashboard showing financial metrics for Portfolio."""

    model = Project
    template_name = "portfolio/portfolio_dashboard.html"
    context_object_name = "projects"

    filter_form: FilterForm | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_form = None

    def setup(self, request, *args, **kwargs):
        """Initialize view during setup."""
        super().setup(request, *args, **kwargs)

    def get_breadcrumbs(self: "PortfolioDashboardView") -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": None},
            {"title": "Dashboard", "url": None},
        ]

    def get_queryset(self: "PortfolioDashboardView") -> QuerySet[Project]:
        """Get filtered projects for dashboard view."""
        # Initialize filter form with user's projects
        user: Account = self.request.user  # type: ignore
        projects = user.get_projects.order_by("-created_at")

        # Initialize filter form with the base queryset
        self.filter_form = FilterForm(
            self.request.GET or {}, user=user, projects_queryset=projects
        )

        if not self.filter_form or not self.filter_form.is_valid():
            # Return unfiltered queryset if form is invalid
            return projects

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
        if not user.portfolio:
            new_portfolio: Portfolio = Portfolio.objects.create()  #
            new_portfolio.users.add(user)
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
        active_projects = portfolio.get_active_projects(category_filter)
        active_count = active_projects.count()
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


class PortfolioReportMixin(UserHasGroupGenericMixin, BreadcrumbMixin, TemplateView):
    """Base mixin for portfolio reports."""

    permissions = ["consultant", "contractor"]

    def get_portfolio(self) -> Portfolio:
        """Get the current user's portfolio."""
        user: Account = self.request.user  # type: ignore
        if not user.portfolio:
            new_portfolio = Portfolio.objects.create()
            new_portfolio.users.add(user)
            user.refresh_from_db()
        return user.portfolio  # type: ignore

    def get_active_projects(self) -> list[Project]:
        """Get active projects for the current user."""
        return list(
            Project.objects.filter(
                users=self.request.user,
                status=Project.Status.ACTIVE,
            ).order_by("name")
        )


class ComplianceReportView(PortfolioReportMixin):
    """Portfolio Compliance Report covering Contractual, Administrative, Final Account."""

    template_name = "portfolio/reports/compliance_report.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": "/"},
            {"title": "Reports", "url": None},
            {"title": "Compliance Report", "url": None},
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        portfolio = self.get_portfolio()
        projects = self.get_active_projects()

        # Get filter parameters
        party_filter = self.request.GET.get("party", "")  # contractor or consultant

        # Build report data per project
        report_data = []
        for project in projects:
            # Get responsible party filter
            party_q = Q()
            if party_filter:
                party_q = Q(responsible_party__groups__name__iexact=party_filter)

            # Contractual Compliance stats
            contractual_items = ContractualCompliance.objects.filter(
                project=project, deleted=False
            ).filter(party_q)
            contractual_total = contractual_items.count()
            contractual_completed = contractual_items.filter(
                status=ContractualCompliance.Status.COMPLETED
            ).count()
            contractual_overdue = contractual_items.filter(
                status=ContractualCompliance.Status.OVERDUE
            ).count()
            contractual_pct = (
                round(contractual_completed / contractual_total * 100, 1)
                if contractual_total > 0
                else 0
            )

            # Administrative Compliance stats
            admin_items = AdministrativeCompliance.objects.filter(
                project=project, deleted=False
            ).filter(party_q)
            admin_total = admin_items.count()
            admin_completed = admin_items.filter(
                status=AdministrativeCompliance.Status.APPROVED
            ).count()
            admin_overdue = admin_items.filter(
                status=AdministrativeCompliance.Status.OVERDUE
            ).count()
            admin_pct = (
                round(admin_completed / admin_total * 100, 1) if admin_total > 0 else 0
            )

            # Final Account Compliance stats
            final_items = FinalAccountCompliance.objects.filter(
                project=project, deleted=False
            ).filter(party_q)
            final_total = final_items.count()
            final_completed = final_items.filter(
                status=FinalAccountCompliance.Status.APPROVED
            ).count()
            final_pct = (
                round(final_completed / final_total * 100, 1) if final_total > 0 else 0
            )

            # Overall compliance
            total_items = contractual_total + admin_total + final_total
            total_completed = contractual_completed + admin_completed + final_completed
            overall_pct = (
                round(total_completed / total_items * 100, 1) if total_items > 0 else 0
            )

            report_data.append(
                {
                    "project": project,
                    "contractual": {
                        "total": contractual_total,
                        "completed": contractual_completed,
                        "overdue": contractual_overdue,
                        "percentage": contractual_pct,
                    },
                    "administrative": {
                        "total": admin_total,
                        "completed": admin_completed,
                        "overdue": admin_overdue,
                        "percentage": admin_pct,
                    },
                    "final_account": {
                        "total": final_total,
                        "completed": final_completed,
                        "percentage": final_pct,
                    },
                    "overall_percentage": overall_pct,
                    "total_overdue": contractual_overdue + admin_overdue,
                }
            )

        # Calculate portfolio totals
        total_contractual = sum(r["contractual"]["total"] for r in report_data)
        total_admin = sum(r["administrative"]["total"] for r in report_data)
        total_final = sum(r["final_account"]["total"] for r in report_data)
        completed_contractual = sum(r["contractual"]["completed"] for r in report_data)
        completed_admin = sum(r["administrative"]["completed"] for r in report_data)
        completed_final = sum(r["final_account"]["completed"] for r in report_data)

        context["report_data"] = report_data
        context["portfolio"] = portfolio
        context["party_filter"] = party_filter
        context["summary"] = {
            "contractual_pct": (
                round(completed_contractual / total_contractual * 100, 1)
                if total_contractual > 0
                else 0
            ),
            "admin_pct": (
                round(completed_admin / total_admin * 100, 1) if total_admin > 0 else 0
            ),
            "final_pct": (
                round(completed_final / total_final * 100, 1) if total_final > 0 else 0
            ),
            "total_overdue": sum(r["total_overdue"] for r in report_data),
        }

        return context


class ImpactReportView(PortfolioReportMixin):
    """Portfolio Impact Report covering Jobs, Poverty, Local Subcontracts, Local Spend, ROI."""

    template_name = "portfolio/reports/impact_report.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": "/"},
            {"title": "Reports", "url": None},
            {"title": "Impact Report", "url": None},
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        portfolio = self.get_portfolio()
        projects = self.get_active_projects()

        # Get filter parameters
        demographic_filter = self.request.GET.get("demographic", "")
        locality_filter = self.request.GET.get("locality", "")

        # Build report data per project
        report_data = []
        for project in projects:
            # Build filter for impacts
            impact_q = Q(project=project, deleted=False)
            if demographic_filter:
                impact_q &= Q(demographic=demographic_filter)
            if locality_filter:
                impact_q &= Q(locality=locality_filter)

            impacts = ProjectImpact.objects.filter(impact_q)

            # Aggregate impact data
            aggregated = impacts.aggregate(
                total_jobs_created=Coalesce(Sum("jobs_created"), 0),
                total_jobs_retained=Coalesce(Sum("jobs_retained"), 0),
                total_poverty_beneficiaries=Coalesce(Sum("poverty_beneficiaries"), 0),
                total_poverty_spend=Coalesce(Sum("poverty_spend"), Decimal("0.00")),
                total_local_subcontracts=Coalesce(Sum("local_subcontract_count"), 0),
                total_local_subcontract_value=Coalesce(
                    Sum("local_subcontract_value"), Decimal("0.00")
                ),
                total_local_spend=Coalesce(Sum("local_spend_amount"), Decimal("0.00")),
                total_investment=Coalesce(Sum("investment_amount"), Decimal("0.00")),
                total_return=Coalesce(Sum("return_amount"), Decimal("0.00")),
            )

            # Calculate ROI
            roi = None
            if aggregated["total_investment"] > 0:
                roi = (
                    (aggregated["total_return"] - aggregated["total_investment"])
                    / aggregated["total_investment"]
                    * 100
                )

            report_data.append(
                {
                    "project": project,
                    "jobs_created": aggregated["total_jobs_created"],
                    "jobs_retained": aggregated["total_jobs_retained"],
                    "total_jobs": (
                        aggregated["total_jobs_created"]
                        + aggregated["total_jobs_retained"]
                    ),
                    "poverty_beneficiaries": aggregated["total_poverty_beneficiaries"],
                    "poverty_spend": aggregated["total_poverty_spend"],
                    "local_subcontracts": aggregated["total_local_subcontracts"],
                    "local_subcontract_value": aggregated[
                        "total_local_subcontract_value"
                    ],
                    "local_spend": aggregated["total_local_spend"],
                    "investment": aggregated["total_investment"],
                    "return_amount": aggregated["total_return"],
                    "roi": roi,
                }
            )

        # Calculate portfolio totals
        context["report_data"] = report_data
        context["portfolio"] = portfolio
        context["demographic_filter"] = demographic_filter
        context["locality_filter"] = locality_filter
        context["demographic_choices"] = ProjectImpact.Demographic.choices
        context["locality_choices"] = ProjectImpact.Locality.choices
        context["summary"] = {
            "total_jobs": sum(r["total_jobs"] for r in report_data),
            "total_poverty_beneficiaries": sum(
                r["poverty_beneficiaries"] for r in report_data
            ),
            "total_local_subcontracts": sum(
                r["local_subcontracts"] for r in report_data
            ),
            "total_local_spend": sum(r["local_spend"] for r in report_data),
        }

        return context


class RiskReportView(PortfolioReportMixin):
    """Portfolio Risk Report covering Time Impact and Cost Impact."""

    template_name = "portfolio/reports/risk_report.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": "/"},
            {"title": "Reports", "url": None},
            {"title": "Risk Report", "url": None},
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        portfolio = self.get_portfolio()
        projects = self.get_active_projects()

        # Get filter parameters
        category_filter = self.request.GET.get("category", "")

        # Build report data per project
        report_data = []
        for project in projects:
            # Build filter for risks
            risk_q = Q(project=project, deleted=False, is_active=True)
            if category_filter:
                risk_q &= Q(category=category_filter)

            risks = Risk.objects.filter(risk_q)

            # Aggregate risk data
            risk_count = risks.count()
            total_cost_impact = risks.aggregate(
                total=Coalesce(Sum("cost_impact"), Decimal("0.00"))
            )["total"]
            estimated_cost_impact = sum(r.estimated_cost_impact for r in risks)

            # Calculate time impact
            total_time_days = sum(r.time_impact_days or 0 for r in risks)
            estimated_time_days = sum(
                float(r.estimated_time_impact_days or 0) for r in risks
            )

            # Risk breakdown by category
            category_breakdown = (
                risks.values("category").annotate(count=Count("id")).order_by("-count")
            )

            report_data.append(
                {
                    "project": project,
                    "risk_count": risk_count,
                    "total_cost_impact": total_cost_impact,
                    "estimated_cost_impact": estimated_cost_impact,
                    "total_time_days": total_time_days,
                    "estimated_time_days": round(estimated_time_days, 1),
                    "category_breakdown": list(category_breakdown),
                }
            )

        # Calculate portfolio totals
        context["report_data"] = report_data
        context["portfolio"] = portfolio
        context["category_filter"] = category_filter
        context["category_choices"] = Risk.RiskCategory.choices
        context["summary"] = {
            "total_risks": sum(r["risk_count"] for r in report_data),
            "total_cost_impact": sum(r["total_cost_impact"] for r in report_data),
            "estimated_cost_impact": sum(
                r["estimated_cost_impact"] for r in report_data
            ),
            "total_time_days": sum(r["total_time_days"] for r in report_data),
            "estimated_time_days": round(
                sum(r["estimated_time_days"] for r in report_data), 1
            ),
        }

        return context
