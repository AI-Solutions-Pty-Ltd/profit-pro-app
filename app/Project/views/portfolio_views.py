"""Views for Project app."""

import json
from datetime import datetime, timedelta
from typing import cast

from django.db.models import QuerySet, Sum
from django.views.generic import (
    ListView,
)

from app.Account.models import Account
from app.BillOfQuantities.models import ActualTransaction, PaymentCertificate
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import FilterForm
from app.Project.models import Project


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

    def get_breadcrumbs(self):
        return [
            {"title": "Portfolio", "url": None},
            {"title": "Dashboard", "url": None},
        ]

    def get_queryset(self) -> QuerySet[Project]:
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

    def get_context_data(self, **kwargs):
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)
        projects = context["projects"]

        # Add the already-validated form to context
        context["filter_form"] = self.filter_form

        dashboard_data = []
        for project in projects:
            # Get contract value
            contract_value = project.get_total_contract_value

            # Get cumulative certified to date (sum of all approved payment certificates)
            certified_amount = (
                ActualTransaction.objects.filter(
                    line_item__project=project,
                    payment_certificate__status=PaymentCertificate.Status.APPROVED,
                ).aggregate(total=Sum("total_price"))["total"]
                or 0
            )

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
            current_date = datetime.now()
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
        portfolio = cast(Account, self.request.user).portfolio
        context["portfolio"] = portfolio
        context["current_date"] = datetime.now()

        # Generate 12 months of CPI/SPI data for charts
        performance_data = self._get_performance_chart_data(portfolio)
        context["performance_labels"] = json.dumps(performance_data["labels"])
        context["cpi_data"] = json.dumps(performance_data["cpi"])
        context["spi_data"] = json.dumps(performance_data["spi"])
        context["current_cpi"] = performance_data["current_cpi"]
        context["current_spi"] = performance_data["current_spi"]

        return context

    def _get_performance_chart_data(self, portfolio) -> dict:
        """Generate 12 months of CPI/SPI data for portfolio."""
        labels = []
        cpi_values = []
        spi_values = []

        current_date = datetime.now()

        # Generate data for last 12 months (oldest to newest)
        for i in range(11, -1, -1):
            # Calculate the date for this month
            month_date = current_date - timedelta(days=i * 30)
            # Normalize to first of month
            month_date = month_date.replace(day=1)

            labels.append(month_date.strftime("%b %Y"))

            if portfolio:
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
            else:
                cpi_values.append(None)
                spi_values.append(None)

        return {
            "labels": labels,
            "cpi": cpi_values,
            "spi": spi_values,
            "current_cpi": cpi_values[-1] if cpi_values else None,
            "current_spi": spi_values[-1] if spi_values else None,
        }
