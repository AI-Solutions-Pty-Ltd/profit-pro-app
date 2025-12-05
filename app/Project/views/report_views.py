"""Views for Portfolio Reports."""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from dateutil.relativedelta import relativedelta
from django.db.models import QuerySet, Sum
from django.urls import reverse
from django.views.generic import ListView, TemplateView

from app.BillOfQuantities.models import Forecast, PaymentCertificate
from app.core.Utilities.dates import get_end_of_month
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import FilterForm
from app.Project.models import Portfolio, Project
from app.Project.models.planned_value_models import PlannedValue


class FinancialReportView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Financial Report - Project List with Budget, Forecast, Variances, Certified, CPI & SPI."""

    model = Project
    template_name = "portfolio/reports/financial_report.html"
    context_object_name = "projects"
    permissions = ["consultant", "contractor"]

    filter_form: FilterForm | None = None

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        self.filter_form = FilterForm(request.GET or {})

    def get_breadcrumbs(self: "FinancialReportView") -> list[BreadcrumbItem]:
        """Return breadcrumbs for financial report."""
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
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
        """Get active projects for the user's portfolio with optional category filter."""
        projects = Project.objects.filter(
            account=self.request.user,
            status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED],
        )

        # Apply category filter if selected
        if self.filter_form and self.filter_form.is_valid():
            category = self.filter_form.cleaned_data.get("category")
            if category:
                projects = projects.filter(category=category)

        return projects

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
            "cost_variance": Decimal("0.00"),
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

            # Variance (Budget - Forecast: negative = over budget = bad)
            variance = budget - forecast_total

            # Certified (Total certified amount to date - all approved payment certificates)
            certified = project.payment_certificates.filter(
                status=PaymentCertificate.Status.APPROVED
            ).aggregate(total=Sum("actual_transactions__total_price"))[
                "total"
            ] or Decimal("0.00")

            # Cost Variance (Earned Value - Actual Cost)
            try:
                cost_variance = project.cost_variance(current_date) or Decimal("0.00")
            except (ZeroDivisionError, TypeError):
                cost_variance = Decimal("0.00")

            # CPI & SPI
            try:
                cpi = project.cost_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                cpi = None

            try:
                spi = project.schedule_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                spi = None

            # Calculate certified percentage (certified / budget)
            certified_percentage = (
                (certified / budget * 100) if budget else Decimal("0.00")
            )

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
                    "certified_percentage": certified_percentage,
                    "cost_variance": cost_variance,
                    "cpi": cpi,
                    "spi": spi,
                }
            )

            # Accumulate totals
            totals["budget"] += budget
            totals["forecast"] += forecast_total
            totals["variance"] += variance
            totals["certified"] += certified
            totals["cost_variance"] += cost_variance

        # Calculate total variance percentage
        totals["variance_percentage"] = (
            (totals["variance"] / totals["budget"] * 100)
            if totals["budget"]
            else Decimal("0.00")
        )

        # Calculate total certified percentage
        totals["certified_percentage"] = (
            (totals["certified"] / totals["budget"] * 100)
            if totals["budget"]
            else Decimal("0.00")
        )

        # Get sort parameter from request
        sort_by = self.request.GET.get("sort", "")
        if sort_by == "variance_asc":
            # Sort by variance ascending (worst variance first)
            report_data.sort(
                key=lambda x: x["variance"] or Decimal("0"),
            )
        elif sort_by == "variance_desc":
            # Sort by variance descending (best variance first)
            report_data.sort(
                key=lambda x: -(x["variance"] or Decimal("0")),
            )
        elif sort_by == "cpi_asc":
            # Sort by CPI ascending (worst CPI first)
            report_data.sort(
                key=lambda x: (x["cpi"] is None, x["cpi"] or Decimal("0")),
            )
        elif sort_by == "cpi_desc":
            # Sort by CPI descending (best CPI first)
            report_data.sort(
                key=lambda x: (x["cpi"] is None, -(x["cpi"] or Decimal("0"))),
            )
        elif sort_by == "spi_asc":
            # Sort by SPI ascending (worst SPI first)
            report_data.sort(
                key=lambda x: (x["spi"] is None, x["spi"] or Decimal("0")),
            )
        elif sort_by == "spi_desc":
            # Sort by SPI descending (best SPI first)
            report_data.sort(
                key=lambda x: (x["spi"] is None, -(x["spi"] or Decimal("0"))),
            )
        else:
            # Default sort by project name
            report_data.sort(key=lambda x: x["project"].name.lower())

        context["report_data"] = report_data
        context["totals"] = totals
        context["current_date"] = current_date
        context["portfolio"]: Portfolio = self.request.user.portfolio  # type: ignore
        context["filter_form"] = self.filter_form
        context["current_sort"] = sort_by

        return context


class ScheduleReportView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Schedule Report - Project List with Planned Time, Forecast, Actual."""

    model = Project
    template_name = "portfolio/reports/schedule_report.html"
    context_object_name = "projects"
    permissions = ["consultant", "contractor"]

    filter_form: FilterForm | None = None

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        self.filter_form = FilterForm(request.GET or {})

    def get_breadcrumbs(self: "ScheduleReportView") -> list[BreadcrumbItem]:
        """Return breadcrumbs for schedule report."""
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
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
        """Get active projects for the user's portfolio with optional category filter."""
        projects = Project.objects.filter(
            account=self.request.user,
            status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED],
        )

        # Apply category filter if selected
        if self.filter_form and self.filter_form.is_valid():
            category = self.filter_form.cleaned_data.get("category")
            if category:
                projects = projects.filter(category=category)

        return projects

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

            # Percentage complete (based on certified vs budget)
            budget = project.get_original_contract_value or Decimal("0.00")
            certified = project.actual_cost() or Decimal("0.00")
            percent_work_complete = (
                (certified / budget * 100) if budget else Decimal("0.00")
            )

            # Forecast Completion date
            # Calculate based on % complete and elapsed time
            forecast_completion = None
            if planned_start and planned_duration and percent_work_complete > 0:
                # Estimate remaining duration based on progress
                days_elapsed = (current_date.date() - planned_start).days
                if days_elapsed > 0 and percent_work_complete > 0:
                    # Estimated total duration = days_elapsed / (percent_complete / 100)
                    estimated_total_days = int(
                        days_elapsed / (float(percent_work_complete) / 100)
                    )
                    forecast_completion = planned_start + relativedelta(
                        days=estimated_total_days
                    )
                else:
                    forecast_completion = planned_end
            elif planned_end:
                forecast_completion = planned_end

            # Variance (days) = Planned End - Forecast Completion
            # Negative means behind schedule, Positive means ahead
            variance_days = None
            if planned_end and forecast_completion:
                variance_days = (planned_end - forecast_completion).days

            # SPI
            try:
                spi = project.schedule_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                spi = None

            # Schedule Variance (Value) = EV - PV
            # EV (Earned Value) = Budget * % Complete
            # PV (Planned Value) = Budget * Planned % Complete at this date
            schedule_variance_value = None
            earned_value = budget * (percent_work_complete / 100) if budget else None

            if planned_start and planned_end and planned_duration and budget:
                days_elapsed = (current_date.date() - planned_start).days
                if days_elapsed >= 0:
                    # Planned % complete based on time elapsed
                    planned_percent = min(
                        Decimal(days_elapsed) / Decimal(planned_duration) * 100,
                        Decimal("100"),
                    )
                    planned_value = budget * (planned_percent / 100)
                    if earned_value is not None:
                        schedule_variance_value = earned_value - planned_value

            report_data.append(
                {
                    "project": project,
                    "planned_start": planned_start,
                    "planned_end": planned_end,
                    "planned_duration": planned_duration,
                    "forecast_completion": forecast_completion,
                    "variance_days": variance_days,
                    "percent_work_complete": percent_work_complete,
                    "spi": spi,
                    "schedule_variance_value": schedule_variance_value,
                }
            )

        # Get sort parameter from request
        sort_by = self.request.GET.get("sort", "")
        if sort_by == "variance_asc":
            # Sort by schedule variance ascending (most behind first)
            report_data.sort(
                key=lambda x: (
                    x["schedule_variance_value"] is None,
                    x["schedule_variance_value"] or Decimal("0"),
                )
            )
        elif sort_by == "variance_desc":
            # Sort by schedule variance descending (most ahead first)
            report_data.sort(
                key=lambda x: (
                    x["schedule_variance_value"] is None,
                    -(x["schedule_variance_value"] or Decimal("0")),
                )
            )
        else:
            # Default sort by project name
            report_data.sort(key=lambda x: x["project"].name.lower())

        context["report_data"] = report_data
        context["current_date"] = current_date
        context["portfolio"]: Portfolio = self.request.user.portfolio  # type: ignore
        context["filter_form"] = self.filter_form
        context["current_sort"] = sort_by

        return context


class CashflowReportView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Cashflow Report - Current Month Actuals and Next 3 Months Forecast."""

    model = Project
    template_name = "portfolio/reports/cashflow_report.html"
    context_object_name = "projects"
    permissions = ["consultant", "contractor"]

    filter_form: FilterForm | None = None

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        self.filter_form = FilterForm(request.GET or {})

    def get_breadcrumbs(self: "CashflowReportView") -> list[BreadcrumbItem]:
        """Return breadcrumbs for cashflow report."""
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title="Reports",
                url=None,
            ),
            BreadcrumbItem(
                title="Cashflow Report",
                url=None,
            ),
        ]

    def get_queryset(self: "CashflowReportView") -> QuerySet[Project]:
        """Get active projects for the user's portfolio with optional category filter."""
        projects = Project.objects.filter(
            account=self.request.user,
            status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED],
        ).order_by("name")

        # Apply category filter if selected
        if self.filter_form and self.filter_form.is_valid():
            category = self.filter_form.cleaned_data.get("category")
            if category:
                projects = projects.filter(category=category)

        return projects

    def get_context_data(self: "CashflowReportView", **kwargs: Any) -> dict[str, Any]:
        """Add cashflow metrics to context."""
        context = super().get_context_data(**kwargs)
        projects: QuerySet[Project] = context["projects"]
        current_date = datetime.now()

        # Calculate current month and next 3 months
        current_month = get_end_of_month(current_date)
        month_1 = current_month + relativedelta(months=1)
        month_2 = current_month + relativedelta(months=2)
        month_3 = current_month + relativedelta(months=3)

        report_data = []
        totals = {
            "current_cashflow": Decimal("0.00"),
            "month_1_forecast": Decimal("0.00"),
            "month_2_forecast": Decimal("0.00"),
            "month_3_forecast": Decimal("0.00"),
            "total_forecast": Decimal("0.00"),
        }

        for project in projects:
            # Current Cashflow (from current month approved payment certificates)
            if project.start_date and project.start_date > current_month.date():
                current_cashflow = "Not Started"
            elif project.end_date and project.end_date < current_month.date():
                current_cashflow = "Project Ended"
            else:
                current_month_certs = project.payment_certificates.filter(
                    status=PaymentCertificate.Status.APPROVED,
                    approved_on__year=current_month.year,
                    approved_on__month=current_month.month,
                )
                current_cashflow = Decimal("0.00")
                for cert in current_month_certs:
                    current_cashflow += cert.current_claim_total or Decimal("0.00")

            total_3_month_forecast = Decimal("0.00")
            # Get latest cashflow forecast for next 3 months
            # Month 1
            if project.start_date and project.start_date > month_1.date():
                month_1_forecast = "Not Started"
            elif project.end_date and project.end_date < month_1.date():
                month_1_forecast = "Project Ended"
            else:
                month_1_forecast = self._get_forecast_for_period(project, month_1)
                totals["month_1_forecast"] += month_1_forecast
            # Month 2
            if project.start_date and project.start_date > month_2.date():
                month_2_forecast = "Not Started"
            elif project.end_date and project.end_date < month_2.date():
                month_2_forecast = "Project Ended"
            else:
                month_2_forecast = self._get_forecast_for_period(project, month_2)
                totals["month_2_forecast"] += month_2_forecast
            # Month 3
            if project.start_date and project.start_date > month_3.date():
                month_3_forecast = "Not Started"
            elif project.end_date and project.end_date < month_3.date():
                month_3_forecast = "Project Ended"
            else:
                month_3_forecast = self._get_forecast_for_period(project, month_3)
                totals["month_3_forecast"] += month_3_forecast

            report_data.append(
                {
                    "project": project,
                    "current_cashflow": current_cashflow,
                    "month_1_forecast": month_1_forecast,
                    "month_2_forecast": month_2_forecast,
                    "month_3_forecast": month_3_forecast,
                    "total_forecast": total_3_month_forecast,
                }
            )

            # Accumulate totals
            if isinstance(current_cashflow, Decimal):
                totals["current_cashflow"] += current_cashflow
            totals["total_forecast"] += total_3_month_forecast

        context["report_data"] = report_data
        context["totals"] = totals
        context["current_date"] = current_date
        context["current_month"] = current_month
        context["month_1"] = month_1
        context["month_2"] = month_2
        context["month_3"] = month_3
        context["portfolio"]: Portfolio = self.request.user.portfolio  # type: ignore
        context["filter_form"] = self.filter_form

        return context

    def _get_forecast_for_period(
        self: "CashflowReportView", project: Project, period: datetime
    ) -> Decimal:
        """Get forecast value for a specific period from CashflowForecast."""
        forecast = PlannedValue.objects.filter(
            project=project,
            period__year=period.year,
            period__month=period.month,
        ).first()

        if forecast:
            return forecast.forecast_value or Decimal("0.00")
        return Decimal("0.00")


class TrendReportView(UserHasGroupGenericMixin, BreadcrumbMixin, TemplateView):
    """Trend Analysis Report - 12 Month Planned vs Actual vs Forecast vs Budget."""

    template_name = "portfolio/reports/trend_report.html"
    permissions = ["consultant", "contractor"]

    filter_form: FilterForm | None = None

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        self.filter_form = FilterForm(request.GET or {})

    def get_breadcrumbs(self: "TrendReportView") -> list[BreadcrumbItem]:
        """Return breadcrumbs for trend report."""
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title="Reports",
                url=None,
            ),
            BreadcrumbItem(
                title="Trend Analysis",
                url=None,
            ),
        ]

    def get_context_data(self: "TrendReportView", **kwargs: Any) -> dict[str, Any]:
        """Add trend analysis data to context."""
        context = super().get_context_data(**kwargs)
        current_date = datetime.now()

        portfolio: Portfolio | None = self.request.user.portfolio  # type: ignore
        context["portfolio"] = portfolio
        context["current_date"] = current_date
        context["filter_form"] = self.filter_form

        if not portfolio:
            context["cashflow_labels"] = "[]"
            context["planned_data"] = "[]"
            context["actual_data"] = "[]"
            context["forecast_data"] = "[]"
            context["budget_data"] = "[]"
            return context

        # Get category filter
        category_filter = (
            self.filter_form.cleaned_data.get("category")
            if self.filter_form and self.filter_form.is_valid()
            else None
        )

        # Generate 12 months of Planned vs Actual vs Forecast vs Budget data
        cashflow_data = self._get_cashflow_chart_data(
            portfolio, category=category_filter
        )
        context["cashflow_labels"] = json.dumps(cashflow_data["labels"])
        context["planned_data"] = json.dumps(cashflow_data["planned"])
        context["actual_data"] = json.dumps(cashflow_data["actual"])
        context["forecast_data"] = json.dumps(cashflow_data["forecast"])
        context["budget_data"] = json.dumps(cashflow_data["budget"])

        return context

    def _get_cashflow_chart_data(
        self: "TrendReportView", portfolio: Portfolio, category=None
    ) -> dict:
        """Generate 12 months of Planned vs Actual vs Forecast vs Budget data."""
        labels = []
        planned_values = []
        actual_values = []
        forecast_values = []
        budget_values = []

        current_date = datetime.now()
        # Monthly budget = total budget / 12 (simplified distribution)
        total_budget = portfolio.get_total_original_budget(category)
        monthly_budget = float(total_budget / 12) if total_budget else 0

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
