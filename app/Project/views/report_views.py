"""Views for Portfolio Reports."""

import csv
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Any

from dateutil.relativedelta import relativedelta
from django.db.models import Q, QuerySet, Sum
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, TemplateView
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.BillOfQuantities.models import (
    ContractualCorrespondence,
    ContractVariation,
    Forecast,
    PaymentCertificate,
)
from app.core.Utilities.dates import get_end_of_month
from app.core.Utilities.mixins import (
    BreadcrumbItem,
    BreadcrumbMixin,
)
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.core.Utilities.subscription_and_role_mixin import (
    SubscriptionAndRoleRequiredMixin,
)
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import (
    AdministrativeCompliance,
    ContractualCompliance,
    FinalAccountCompliance,
    Milestone,
    PlannedValue,
    Portfolio,
    Project,
    ProjectCategory,
    ProjectDocument,
    ProjectReportSummary,
    Risk,
    RiskStatus,
    Role,
)
from app.Project.projects.project_forms import ProjectFilterForm
from app.SiteManagement.models import (
    RFI,
    BiWeeklyQualityReport,
    BiWeeklySafetyReport,
    EarlyWarning,
    EarlyWarningStatus,
    Incident,
    IncidentStatus,
    IncidentType,
    LabourLog,
    MaterialsLog,
    MeetingAction,
    MeetingActionStatus,
    MeetingDecision,
    NCRStatus,
    NCRType,
    NonConformance,
    PlantEquipment,
    ProductivityLog,
    ProgressTracker,
    QualityControl,
    RFIStatus,
    SiteInstruction,
    SiteInstructionStatus,
)


class ProjectAccessMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    """Mixin to add project to context."""

    def get_queryset(self):
        user: Account = self.request.user  # type: ignore
        user_projects = user.get_projects
        return user_projects.filter(
            status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED],
            project_roles__user=user,
        )


class FinancialReportView(SubscriptionRequiredMixin, ProjectAccessMixin, ListView):
    """Financial Report - Project List with Budget, Forecast, Variances, Certified, CPI & SPI."""

    model = Project
    template_name = "portfolio/reports/financial_report.html"
    context_object_name = "projects"
    permissions = ["contractor"]
    required_tiers = [Subscription.FREE_TIER]

    filter_form: ProjectFilterForm | None = None

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        from app.Project.models import (
            Company,
            ProjectDiscipline,
            ProjectSubCategory,
        )

        # Get user's projects
        user: Account = self.request.user  # type: ignore
        projects = user.get_projects.order_by("-created_at")

        # Get unique clients and contractors from user's projects
        client_queryset = Company.objects.filter(
            client_projects__in=projects
        ).distinct()
        contractor_queryset = Company.objects.filter(
            contractor_projects__in=projects
        ).distinct()

        # Get unique categories, subcategories and disciplines from user's projects
        category_queryset = ProjectCategory.objects.filter(
            projects__in=projects
        ).distinct()
        subcategory_queryset = ProjectSubCategory.objects.filter(
            projects__in=projects
        ).distinct()
        discipline_queryset = ProjectDiscipline.objects.filter(
            projects__in=projects
        ).distinct()

        self.filter_form = ProjectFilterForm(
            request.GET or {},
            user=self.request.user,  # type: ignore
            projects_queryset=projects,
            client_queryset=client_queryset,
            contractor_queryset=contractor_queryset,
            category_queryset=category_queryset,
            subcategory_queryset=subcategory_queryset,
            discipline_queryset=discipline_queryset,
        )

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
        """Get filtered projects for financial report view."""
        # Initialize filter form with user's projects
        user: Account = self.request.user  # type: ignore
        projects = user.get_projects.order_by("-created_at")

        # Apply filters if valid
        if self.filter_form and self.filter_form.is_valid():
            category = self.filter_form.cleaned_data.get("project_category")
            if category:
                projects = projects.filter(project_category=category)
            subcategory = self.filter_form.cleaned_data.get("project_subcategory")
            if subcategory:
                projects = projects.filter(project_sub_category=subcategory)
            discipline = self.filter_form.cleaned_data.get("project_discipline")
            if discipline:
                projects = projects.filter(project_discipline=discipline)
            selected_project = self.filter_form.cleaned_data.get("projects")
            if selected_project:
                projects = projects.filter(pk=selected_project.pk)
            consultant = self.filter_form.cleaned_data.get("consultant")
            if consultant:
                projects = projects.filter(lead_consultant=consultant)
            client = self.filter_form.cleaned_data.get("client")
            if client:
                projects = projects.filter(client=client)
            contractor = self.filter_form.cleaned_data.get("contractor")
            if contractor:
                projects = projects.filter(contractor=contractor)

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
            budget = project.original_contract_value or Decimal("0.00")

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
                cost_variance = project.get_cost_variance(current_date) or Decimal(
                    "0.00"
                )
            except (ZeroDivisionError, TypeError):
                cost_variance = Decimal("0.00")

            # CPI & SPI
            try:
                cpi = project.get_cost_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                cpi = None

            try:
                spi = project.get_schedule_performance_index(current_date)
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


class ScheduleReportView(SubscriptionRequiredMixin, ProjectAccessMixin, ListView):
    """Schedule Report - Project List with Start/End Dates, Durations, Progress & SPI."""

    model = Project
    template_name = "portfolio/reports/schedule_report.html"
    context_object_name = "projects"
    permissions = ["contractor"]
    required_tiers = [Subscription.FREE_TIER]

    filter_form: ProjectFilterForm | None = None

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        from app.Project.models import (
            Company,
            ProjectDiscipline,
            ProjectSubCategory,
        )

        # Get user's projects
        user: Account = self.request.user  # type: ignore
        projects = user.get_projects.order_by("-created_at")

        # Get unique clients and contractors from user's projects
        client_queryset = Company.objects.filter(
            client_projects__in=projects
        ).distinct()
        contractor_queryset = Company.objects.filter(
            contractor_projects__in=projects
        ).distinct()

        # Get unique categories, subcategories and disciplines from user's projects
        category_queryset = ProjectCategory.objects.filter(
            projects__in=projects
        ).distinct()
        subcategory_queryset = ProjectSubCategory.objects.filter(
            projects__in=projects
        ).distinct()
        discipline_queryset = ProjectDiscipline.objects.filter(
            projects__in=projects
        ).distinct()

        self.filter_form = ProjectFilterForm(
            request.GET or {},
            user=self.request.user,  # type: ignore
            projects_queryset=projects,
            client_queryset=client_queryset,
            contractor_queryset=contractor_queryset,
            category_queryset=category_queryset,
            subcategory_queryset=subcategory_queryset,
            discipline_queryset=discipline_queryset,
        )

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
        """Get active projects for the user's portfolio with optional filters."""
        projects = super().get_queryset()

        # Apply filters if valid
        if self.filter_form and self.filter_form.is_valid():
            category = self.filter_form.cleaned_data.get("project_category")
            if category:
                projects = projects.filter(project_category=category)
            subcategory = self.filter_form.cleaned_data.get("project_subcategory")
            if subcategory:
                projects = projects.filter(project_sub_category=subcategory)
            discipline = self.filter_form.cleaned_data.get("project_discipline")
            if discipline:
                projects = projects.filter(project_discipline=discipline)
            selected_project = self.filter_form.cleaned_data.get("projects")
            if selected_project:
                projects = projects.filter(pk=selected_project.pk)
            consultant = self.filter_form.cleaned_data.get("consultant")
            if consultant:
                projects = projects.filter(lead_consultant=consultant)
            client = self.filter_form.cleaned_data.get("client")
            if client:
                projects = projects.filter(client=client)
            contractor = self.filter_form.cleaned_data.get("contractor")
            if contractor:
                projects = projects.filter(contractor=contractor)

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
            budget = project.original_contract_value or Decimal("0.00")
            certified = project.get_actual_cost() or Decimal("0.00")
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
                spi = project.get_schedule_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                spi = None

            # Schedule Variance (Value) = EV - PV
            # Use model methods as source of truth
            schedule_variance_value = project.get_schedule_variance(current_date)

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


class CashflowReportView(SubscriptionRequiredMixin, ProjectAccessMixin, ListView):
    """Cashflow Report - Project List with Monthly Cashflow Projections."""

    model = Project
    template_name = "portfolio/reports/cashflow_report.html"
    context_object_name = "projects"
    permissions = ["contractor"]
    required_tiers = [Subscription.FREE_TIER]

    filter_form: ProjectFilterForm | None = None

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        from app.Project.models import (
            Company,
            ProjectDiscipline,
            ProjectSubCategory,
        )

        # Get user's projects
        user: Account = self.request.user  # type: ignore
        projects = user.get_projects.order_by("-created_at")

        # Get unique clients and contractors from user's projects
        client_queryset = Company.objects.filter(
            client_projects__in=projects
        ).distinct()
        contractor_queryset = Company.objects.filter(
            contractor_projects__in=projects
        ).distinct()

        # Get unique categories, subcategories and disciplines from user's projects
        category_queryset = ProjectCategory.objects.filter(
            projects__in=projects
        ).distinct()
        subcategory_queryset = ProjectSubCategory.objects.filter(
            projects__in=projects
        ).distinct()
        discipline_queryset = ProjectDiscipline.objects.filter(
            projects__in=projects
        ).distinct()

        self.filter_form = ProjectFilterForm(
            request.GET or {},
            user=self.request.user,  # type: ignore
            projects_queryset=projects,
            client_queryset=client_queryset,
            contractor_queryset=contractor_queryset,
            category_queryset=category_queryset,
            subcategory_queryset=subcategory_queryset,
            discipline_queryset=discipline_queryset,
        )

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
        """Get active projects for the user's portfolio with optional filters."""
        projects = super().get_queryset()

        # Apply filters if valid
        if self.filter_form and self.filter_form.is_valid():
            category = self.filter_form.cleaned_data.get("project_category")
            if category:
                projects = projects.filter(project_category=category)
            subcategory = self.filter_form.cleaned_data.get("project_subcategory")
            if subcategory:
                projects = projects.filter(project_sub_category=subcategory)
            discipline = self.filter_form.cleaned_data.get("project_discipline")
            if discipline:
                projects = projects.filter(project_discipline=discipline)
            selected_project = self.filter_form.cleaned_data.get("projects")
            if selected_project:
                projects = projects.filter(pk=selected_project.pk)
            consultant = self.filter_form.cleaned_data.get("consultant")
            if consultant:
                projects = projects.filter(lead_consultant=consultant)
            client = self.filter_form.cleaned_data.get("client")
            if client:
                projects = projects.filter(client=client)
            contractor = self.filter_form.cleaned_data.get("contractor")
            if contractor:
                projects = projects.filter(contractor=contractor)

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


class TrendReportView(SubscriptionRequiredMixin, ProjectAccessMixin, TemplateView):
    """Trend Report - Portfolio-level trends over time."""

    template_name = "portfolio/reports/trend_report.html"
    permissions = ["contractor"]
    required_tiers = [Subscription.FREE_TIER]

    filter_form: ProjectFilterForm | None = None

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        from app.Project.models import (
            Company,
            ProjectDiscipline,
            ProjectSubCategory,
        )

        # Get user's projects
        user: Account = self.request.user  # type: ignore
        projects = user.get_projects.order_by("-created_at")

        # Get unique clients and contractors from user's projects
        client_queryset = Company.objects.filter(
            client_projects__in=projects
        ).distinct()
        contractor_queryset = Company.objects.filter(
            contractor_projects__in=projects
        ).distinct()

        # Get unique categories, subcategories and disciplines from user's projects
        category_queryset = ProjectCategory.objects.filter(
            projects__in=projects
        ).distinct()
        subcategory_queryset = ProjectSubCategory.objects.filter(
            projects__in=projects
        ).distinct()
        discipline_queryset = ProjectDiscipline.objects.filter(
            projects__in=projects
        ).distinct()

        self.filter_form = ProjectFilterForm(
            request.GET or {},
            user=self.request.user,  # type: ignore
            projects_queryset=projects,
            client_queryset=client_queryset,
            contractor_queryset=contractor_queryset,
            category_queryset=category_queryset,
            subcategory_queryset=subcategory_queryset,
            discipline_queryset=discipline_queryset,
        )

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

        # Get filters
        category_filter = None
        project_filter = None
        consultant_filter = None
        if self.filter_form and self.filter_form.is_valid():
            category_filter = self.filter_form.cleaned_data.get("project_category")
            project_filter = self.filter_form.cleaned_data.get("projects")
            consultant_filter = self.filter_form.cleaned_data.get("consultant")

        # Generate 12 months of Planned vs Actual vs Forecast vs Budget data
        cashflow_data = self._get_cashflow_chart_data(
            portfolio,
            category=category_filter,
            selected_project=project_filter,
            consultant=consultant_filter,
        )
        context["cashflow_labels"] = json.dumps(cashflow_data["labels"])
        context["planned_data"] = json.dumps(cashflow_data["planned"])
        context["actual_data"] = json.dumps(cashflow_data["actual"])
        context["forecast_data"] = json.dumps(cashflow_data["forecast"])
        context["budget_data"] = json.dumps(cashflow_data["budget"])

        return context

    def _get_cashflow_chart_data(
        self: "TrendReportView",
        portfolio: Portfolio,
        category=None,
        selected_project=None,
        consultant=None,
    ) -> dict:
        """Generate 12 months of Planned vs Actual vs Forecast vs Budget data."""
        labels = []
        planned_values = []
        actual_values = []
        forecast_values = []
        budget_values = []

        current_date = datetime.now()
        # Get projects to include
        projects = list(self.get_queryset())
        if selected_project:
            projects = [p for p in projects if p.pk == selected_project.pk]
        if consultant:
            projects = [p for p in projects if consultant in p.lead_consultants.all()]

        # Monthly budget = total budget / 12 (simplified distribution)
        total_budget = sum(p.original_contract_value or Decimal("0") for p in projects)
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

            for project in projects:
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

        return {
            "labels": labels,
            "planned": planned_values,
            "actual": actual_values,
            "forecast": forecast_values,
            "budget": budget_values,
        }


class ContractualReportMixin(SubscriptionAndRoleRequiredMixin, BreadcrumbMixin):
    """Access-controlled mixin for project contractual report."""

    project_slug = "project_pk"
    # NAV gate uses a string role named `REPORTS`. The DB may contain that role value.
    roles = [Role.USER, "REPORTS"]
    required_tiers = [Subscription.FREE_TIER]


class ContractualReportView(ContractualReportMixin, TemplateView):
    """Construction Contractual Report (per project, 1/3/6/12-month windows)."""

    template_name = "project/contractual_report.html"

    def get(self, request, *args, **kwargs):
        export_type = (request.GET.get("export") or "").lower()
        register = (request.GET.get("register") or "").lower()
        if export_type == "csv" and register:
            return self._export_register_csv(register)
        if export_type == "pdf" and register:
            return self._export_register_pdf(register)
        return super().get(request, *args, **kwargs)

    def _build_register_export_data(
        self, register: str
    ) -> tuple[list[str], list[list[Any]], str] | None:
        project = self.get_project()
        period_key = (self.request.GET.get("period") or "1m").lower()
        period_start, period_end, _ = self._get_reporting_window(period_key)

        rows: list[list[Any]] = []
        headers: list[str] = []
        filename = f"{register}_{project.pk}_{period_start}_{period_end}"

        if register == "risk":
            headers = [
                "Risk ID",
                "Description",
                "Owner",
                "Status",
                "Impact Value",
                "Mitigation Action",
                "Target Date",
            ]
            queryset = Risk.objects.filter(
                project=project, date__range=(period_start, period_end)
            ).select_related("raised_by")
            for r in queryset:
                owner = "-"
                if r.raised_by:
                    owner = r.raised_by.get_full_name() or r.raised_by.email
                rows.append(
                    [
                        r.reference_number,
                        r.description,
                        owner,
                        r.status,
                        r.cost_impact or 0,
                        r.mitigation_action or "",
                        r.date_closed.isoformat() if r.date_closed else "",
                    ]
                )
        elif register == "variations":
            headers = [
                "CE No.",
                "Description",
                "Date Notified",
                "Status",
                "Time Impact (days)",
                "Impact Value",
                "Decision",
            ]
            queryset = ContractVariation.objects.filter(
                project=project,
                date_identified__isnull=False,
                date_identified__range=(period_start, period_end),
            )
            for v in queryset:
                decision = (
                    "Approved"
                    if v.status == ContractVariation.Status.APPROVED
                    else "Rejected"
                    if v.status == ContractVariation.Status.REJECTED
                    else "Pending"
                )
                rows.append(
                    [
                        v.variation_number,
                        v.title,
                        v.date_identified.isoformat() if v.date_identified else "",
                        v.status,
                        v.time_extension_days or 0,
                        v.variation_amount or 0,
                        decision,
                    ]
                )
        elif register == "early-warning":
            headers = [
                "EW No.",
                "Description",
                "Raised By",
                "Date",
                "Status",
                "Action Taken",
            ]
            queryset = EarlyWarning.objects.filter(
                project=project, date__range=(period_start, period_end)
            )
            for ew in queryset:
                rows.append(
                    [
                        ew.reference_number,
                        ew.subject,
                        ew.from_display if ew.submitted_by else "",
                        ew.date.isoformat() if ew.date else "",
                        ew.status,
                        ew.response or "",
                    ]
                )
        elif register == "documents":
            headers = [
                "Ref No.",
                "Document Title",
                "Category",
                "Revision Date",
                "Notes",
            ]
            queryset = ProjectDocument.objects.filter(
                project=project,
                category__in=[
                    ProjectDocument.DocumentCategory.DRAWINGS,
                    ProjectDocument.DocumentCategory.SPECIFICATIONS,
                ],
                created_at__date__range=(period_start, period_end),
            )
            for d in queryset:
                rows.append(
                    [
                        f"DOC-{d.pk}",
                        d.title,
                        d.get_category_display(),
                        d.created_at.date().isoformat() if d.created_at else "",
                        d.notes or "",
                    ]
                )
        elif register == "communications":
            headers = [
                "Type",
                "Date",
                "Subject",
                "Requires Response",
                "Response Sent",
                "Response Due Date",
            ]
            queryset = ContractualCorrespondence.objects.filter(
                project=project,
                date_of_correspondence__range=(period_start, period_end),
                deleted=False,
            )
            for c in queryset:
                rows.append(
                    [
                        c.correspondence_type,
                        c.date_of_correspondence.isoformat()
                        if c.date_of_correspondence
                        else "",
                        c.subject,
                        "Yes" if c.requires_response else "No",
                        "Yes" if c.response_sent else "No",
                        c.response_due_date.isoformat() if c.response_due_date else "",
                    ]
                )
        else:
            return None

        return headers, rows, filename

    def _export_register_csv(self, register: str) -> HttpResponse:
        export_data = self._build_register_export_data(register)
        if export_data is None:
            return HttpResponse(status=400)
        headers, rows, filename = export_data

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(rows)
        return response

    def _export_register_pdf(self, register: str) -> HttpResponse:
        export_data = self._build_register_export_data(register)
        if export_data is None:
            return HttpResponse(status=400)
        headers, rows, filename = export_data

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 40

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(40, y, f"{register.title()} Register Export")
        y -= 18
        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, " | ".join(headers))
        y -= 14
        pdf.line(40, y, width - 40, y)
        y -= 12

        for row in rows:
            if y < 40:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica", 9)
            row_text = " | ".join(str(v) for v in row)
            if len(row_text) > 155:
                row_text = f"{row_text[:152]}..."
            pdf.drawString(40, y, row_text)
            y -= 12

        pdf.save()
        data = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        response.write(data)
        return response

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title=project.name,
                url=None,
            ),
            BreadcrumbItem(
                title="Contractual Report",
                url=None,
            ),
        ]

    @staticmethod
    def _get_reporting_window(period_key: str) -> tuple[Any, Any, str]:
        """Return (start_date, end_date, label) for 2 weeks / 1/3/6/12 months."""
        from django.utils import timezone

        today = timezone.now().date()
        period_map = {
            "2w": (14, "2 Weeks (Bi-Weekly)"),
            "1m": (1, "1 Month"),
            "3m": (3, "3 Months"),
            "6m": (6, "6 Months"),
            "12m": (12, "12 Months"),
        }
        if period_key == "2w":
            end = today
            start = today - timedelta(days=14)
            label = "2 Weeks (Bi-Weekly)"
        else:
            months, label = period_map.get(period_key, (1, "1 Month"))
            end = today
            start = (today - relativedelta(months=months)) + timedelta(days=1)
        return start, end, label

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        project = self.get_project()

        period_key = (self.request.GET.get("period") or "1m").lower()
        period_start, period_end, period_label = self._get_reporting_window(period_key)
        # Calendar month comparison windows (previous month vs current month)
        current_month_start = period_end.replace(day=1)
        current_month_end = (
            current_month_start + relativedelta(months=1) - timedelta(days=1)
        )
        previous_month_start = (current_month_start - relativedelta(months=1)).replace(
            day=1
        )
        previous_month_end = (
            previous_month_start + relativedelta(months=1) - timedelta(days=1)
        )

        context.update(
            {
                "project": project,
                "period_key": period_key,
                "period_label": period_label,
                "period_start": period_start,
                "period_end": period_end,
                # Used by the nav include
                "tab": "contractual_report",
            }
        )

        # -----------------------------
        # Project Information (Section 1)
        # -----------------------------
        # Get Report Summary for qualitative data
        summary = ProjectReportSummary.objects.filter(
            project=project, period_start__lte=period_end, period_end__gte=period_start
        ).first()

        context["project_status_summary"] = (
            summary.project_status_summary
            if summary and summary.project_status_summary
            else None
        )

        consultants = project.lead_consultants.all()
        context["consultants"] = ", ".join(
            [(c.get_full_name() or c.email or str(c.pk)) for c in consultants]
        )
        context["client"] = project.client.name if project.client else "-"
        context["contractor"] = project.contractor.name if project.contractor else "-"
        context["contract_reference"] = project.contract_number or "-"

        # -----------------------------
        # Registers (Sections 3-10)
        # -----------------------------
        # Risks (Section 4 + overview + appendices)
        risks = (
            Risk.objects.filter(project=project, date__range=(period_start, period_end))
            .select_related("raised_by")
            .order_by("-created_at")
        )
        risks_open_count = risks.filter(status=RiskStatus.OPEN).count()
        risks_closed_count = risks.filter(status=RiskStatus.CLOSED).count()
        risks_to_date = Risk.objects.filter(project=project)
        risks_current_month_qs = Risk.objects.filter(
            project=project, date__range=(current_month_start, current_month_end)
        )
        risks_previous_month_qs = Risk.objects.filter(
            project=project, date__range=(previous_month_start, previous_month_end)
        )
        risks_current_month_count = risks_current_month_qs.count()
        risks_previous_month_count = risks_previous_month_qs.count()
        risks_current_month_open = risks_current_month_qs.filter(
            status=RiskStatus.OPEN
        ).count()
        risks_current_month_closed = risks_current_month_qs.filter(
            status=RiskStatus.CLOSED
        ).count()
        risks_previous_month_open = risks_previous_month_qs.filter(
            status=RiskStatus.OPEN
        ).count()
        risks_previous_month_closed = risks_previous_month_qs.filter(
            status=RiskStatus.CLOSED
        ).count()
        risks_current_month_cost = (
            risks_current_month_qs.aggregate(total=Sum("cost_impact")).get("total") or 0
        )
        risks_previous_month_cost = (
            risks_previous_month_qs.aggregate(total=Sum("cost_impact")).get("total")
            or 0
        )
        risks_window_cost = risks.aggregate(total=Sum("cost_impact")).get("total") or 0

        # Contractual Variations / Compensation Events (Section 5)
        variations = ContractVariation.objects.filter(
            project=project,
            date_identified__isnull=False,
            date_identified__range=(period_start, period_end),
        ).order_by("-created_at")
        variations_closed_qs = variations.filter(
            status__in=[
                ContractVariation.Status.APPROVED,
                ContractVariation.Status.REJECTED,
            ]
        )
        variations_closed_count = variations_closed_qs.count()
        variations_open_count = variations.count() - variations_closed_count
        variations_to_date = ContractVariation.objects.filter(
            project=project, date_identified__isnull=False
        )
        variations_current_month_qs = ContractVariation.objects.filter(
            project=project,
            date_identified__isnull=False,
            date_identified__range=(current_month_start, current_month_end),
        )
        variations_previous_month_qs = ContractVariation.objects.filter(
            project=project,
            date_identified__isnull=False,
            date_identified__range=(previous_month_start, previous_month_end),
        )
        variations_current_month_count = variations_current_month_qs.count()
        variations_previous_month_count = variations_previous_month_qs.count()
        variations_current_month_closed = variations_current_month_qs.filter(
            status__in=[
                ContractVariation.Status.APPROVED,
                ContractVariation.Status.REJECTED,
            ]
        ).count()
        variations_previous_month_closed = variations_previous_month_qs.filter(
            status__in=[
                ContractVariation.Status.APPROVED,
                ContractVariation.Status.REJECTED,
            ]
        ).count()
        variations_current_month_open = (
            variations_current_month_count - variations_current_month_closed
        )
        variations_previous_month_open = (
            variations_previous_month_count - variations_previous_month_closed
        )
        variations_current_month_cost = (
            variations_current_month_qs.aggregate(total=Sum("variation_amount")).get(
                "total"
            )
            or 0
        )
        variations_previous_month_cost = (
            variations_previous_month_qs.aggregate(total=Sum("variation_amount")).get(
                "total"
            )
            or 0
        )
        variations_window_cost = (
            variations.aggregate(total=Sum("variation_amount")).get("total") or 0
        )

        # Early Warnings (Section 6)
        early_warnings = (
            EarlyWarning.objects.filter(
                project=project, date__range=(period_start, period_end)
            )
            .select_related("submitted_by")
            .order_by("-created_at")
        )
        early_warnings_open_count = early_warnings.filter(
            status=EarlyWarningStatus.OPEN
        ).count()
        early_warnings_closed_count = early_warnings.filter(
            status=EarlyWarningStatus.CLOSED
        ).count()
        early_warnings_to_date = EarlyWarning.objects.filter(project=project)
        early_warnings_current_month_count = EarlyWarning.objects.filter(
            project=project, date__range=(current_month_start, current_month_end)
        ).count()
        early_warnings_previous_month_count = EarlyWarning.objects.filter(
            project=project, date__range=(previous_month_start, previous_month_end)
        ).count()

        # Convenience counts used by the template (executive summary key highlights)
        context["risks_open_count"] = risks_open_count
        context["variations_open_count"] = variations_open_count
        context["early_warnings_open_count"] = early_warnings_open_count

        # Drawings + Specifications (Section 7)
        # NOTE: ProjectDocument does not store revision/issued-state; we use created_at as "Revision Date".
        documents_qs = ProjectDocument.objects.filter(
            project=project,
            category__in=[
                ProjectDocument.DocumentCategory.DRAWINGS,
                ProjectDocument.DocumentCategory.SPECIFICATIONS,
            ],
            created_at__date__range=(period_start, period_end),
        ).order_by("-created_at")
        documents_to_date = ProjectDocument.objects.filter(
            project=project,
            category__in=[
                ProjectDocument.DocumentCategory.DRAWINGS,
                ProjectDocument.DocumentCategory.SPECIFICATIONS,
            ],
        )
        documents_current_month_count = ProjectDocument.objects.filter(
            project=project,
            category__in=[
                ProjectDocument.DocumentCategory.DRAWINGS,
                ProjectDocument.DocumentCategory.SPECIFICATIONS,
            ],
            created_at__date__range=(current_month_start, current_month_end),
        ).count()
        documents_previous_month_count = ProjectDocument.objects.filter(
            project=project,
            category__in=[
                ProjectDocument.DocumentCategory.DRAWINGS,
                ProjectDocument.DocumentCategory.SPECIFICATIONS,
            ],
            created_at__date__range=(previous_month_start, previous_month_end),
        ).count()

        # Communications (Section 8)
        correspondences_base = ContractualCorrespondence.objects.filter(
            project=project,
            date_of_correspondence__range=(period_start, period_end),
            deleted=False,
        ).order_by("-date_of_correspondence")
        notices = correspondences_base.filter(
            correspondence_type=ContractualCorrespondence.CorrespondenceType.NOTICE
        )
        instructions = correspondences_base.filter(
            correspondence_type=ContractualCorrespondence.CorrespondenceType.INSTRUCTION
        )
        outstanding_responses = correspondences_base.filter(
            requires_response=True, response_sent=False
        )
        overdue_outstanding_responses = outstanding_responses.filter(
            response_due_date__isnull=False, response_due_date__lt=period_end
        )
        correspondences_current_month_count = ContractualCorrespondence.objects.filter(
            project=project,
            date_of_correspondence__range=(current_month_start, current_month_end),
            deleted=False,
        ).count()
        correspondences_previous_month_count = ContractualCorrespondence.objects.filter(
            project=project,
            date_of_correspondence__range=(previous_month_start, previous_month_end),
            deleted=False,
        ).count()

        # Milestones / progress (Section 2 + Section 10 appendices)
        milestones = Milestone.objects.filter(project=project).order_by(
            "planned_date", "sequence"
        )
        milestones_completed_in_period = milestones.filter(
            actual_date__range=(period_start, period_end)
        )
        milestones_completed_in_period_count = milestones_completed_in_period.count()
        milestones_in_window = (
            milestones.filter(actual_date__range=(period_start, period_end))
            | milestones.filter(forecast_date__range=(period_start, period_end))
            | milestones.filter(planned_date__range=(period_start, period_end))
        )
        milestones_current_month_count = (
            Milestone.objects.filter(
                project=project,
                actual_date__range=(current_month_start, current_month_end),
            ).count()
            + Milestone.objects.filter(
                project=project,
                forecast_date__range=(current_month_start, current_month_end),
            ).count()
            + Milestone.objects.filter(
                project=project,
                planned_date__range=(current_month_start, current_month_end),
            ).count()
        )
        milestones_previous_month_count = (
            Milestone.objects.filter(
                project=project,
                actual_date__range=(previous_month_start, previous_month_end),
            ).count()
            + Milestone.objects.filter(
                project=project,
                forecast_date__range=(previous_month_start, previous_month_end),
            ).count()
            + Milestone.objects.filter(
                project=project,
                planned_date__range=(previous_month_start, previous_month_end),
            ).count()
        )

        # Pick a small "extract" set for key tables
        context.update(
            {
                "risks": risks,
                "variations": variations,
                "early_warnings": early_warnings,
                "documents": documents_qs,
                "notices": notices,
                "instructions": instructions,
                "outstanding_responses": outstanding_responses,
                "milestones_completed_in_period": milestones_completed_in_period,
                "milestones_in_window": milestones_in_window,
                # Overview register counts (Section 3)
                "register_overview": [
                    {
                        "register_type": "Risk Register",
                        "tab_url": f"{reverse('project:risk-list', args=[project.pk])}?status=OPEN",
                        "total_to_date": risks_to_date.count(),
                        "current_entries": risks.count(),
                        "open_items": risks_open_count,
                        "closed_percentage": round(
                            (risks_closed_count / risks.count() * 100), 1
                        )
                        if risks.count()
                        else 0,
                        "open_percentage": round(
                            (risks_open_count / risks.count() * 100), 1
                        )
                        if risks.count()
                        else 0,
                        "impact_value": risks_window_cost,
                    },
                    {
                        "register_type": "Compensation Event / Register/Variations",
                        "tab_url": f"{reverse('bill_of_quantities:variation-list', args=[project.pk])}?status=SUBMITTED",
                        "total_to_date": variations_to_date.count(),
                        "current_entries": variations.count(),
                        "open_items": variations_open_count,
                        "closed_percentage": round(
                            (variations_closed_count / variations.count() * 100), 1
                        )
                        if variations.count()
                        else 0,
                        "open_percentage": round(
                            (variations_open_count / variations.count() * 100), 1
                        )
                        if variations.count()
                        else 0,
                        "impact_value": variations_window_cost,
                    },
                    {
                        "register_type": "Early Warnings",
                        "tab_url": f"{reverse('site_management:early-warning-list', args=[project.pk])}?status=OPEN",
                        "total_to_date": early_warnings_to_date.count(),
                        "current_entries": early_warnings.count(),
                        "open_items": early_warnings_open_count,
                        "closed_percentage": round(
                            (
                                early_warnings_closed_count
                                / early_warnings.count()
                                * 100
                            ),
                            1,
                        )
                        if early_warnings.count()
                        else 0,
                        "open_percentage": round(
                            (early_warnings_open_count / early_warnings.count() * 100),
                            1,
                        )
                        if early_warnings.count()
                        else 0,
                        "impact_value": None,
                    },
                    {
                        "register_type": "Drawings and Specifications",
                        "tab_url": reverse(
                            "project:document-list",
                            args=[
                                project.pk,
                                ProjectDocument.DocumentCategory.DRAWINGS,
                            ],
                        ),
                        "total_to_date": documents_to_date.count(),
                        "current_entries": documents_qs.count(),
                        "open_items": documents_qs.count(),
                        "closed_percentage": 0,
                        "open_percentage": 100 if documents_qs.count() else 0,
                        "impact_value": None,
                    },
                ],
                "appendix_links": {
                    "risk_register": reverse("project:risk-list", args=[project.pk]),
                    "variations_register": reverse(
                        "bill_of_quantities:variation-list", args=[project.pk]
                    ),
                    "early_warning_register": reverse(
                        "site_management:early-warning-list", args=[project.pk]
                    ),
                    "documents_register": reverse(
                        "project:document-list",
                        args=[project.pk, ProjectDocument.DocumentCategory.DRAWINGS],
                    ),
                    "communications_register": reverse(
                        "bill_of_quantities:correspondence-list", args=[project.pk]
                    ),
                },
                # Simple text blocks for executive summary (Section 2)
                "exec_major_risks": list(
                    risks.filter(status=RiskStatus.OPEN).order_by("-cost_impact")[:5]
                ),
                "exec_compensation_summary": {
                    "total": variations.count(),
                    "approved": variations.filter(
                        status=ContractVariation.Status.APPROVED
                    ).count(),
                    "rejected": variations.filter(
                        status=ContractVariation.Status.REJECTED
                    ).count(),
                    "sum_cost_variation": sum(
                        (v.variation_amount or 0) for v in variations
                    ),
                },
                "reporting_window_text": f"{period_start} to {period_end}",
            }
        )

        # -----------------------------
        # Overview + Prioritized recommendations
        # -----------------------------
        # Recommendations (Section 9) - derived from outstanding items, prioritized.
        delayed_milestones = [m for m in milestones_in_window if m.is_delayed]

        def _priority_rank(priority: str) -> int:
            return {"P1": 1, "P2": 2, "P3": 3}.get(priority, 99)

        recommendations: list[dict[str, Any]] = []

        # P1 - critical items
        if overdue_outstanding_responses.exists():
            recommendations.append(
                {
                    "title": "Overdue responses require escalation",
                    "count": overdue_outstanding_responses.count(),
                    "details": "There are correspondences with response due dates earlier than the reporting end date and no response marked as sent.",
                }
            )
        if delayed_milestones:
            recommendations.append(
                {
                    "title": "Delayed milestones impacting programme",
                    "count": len(delayed_milestones),
                    "details": "Milestones show forecast dates later than planned dates within the reporting window.",
                }
            )
        high_cost_risks = list(
            risks.filter(status=RiskStatus.OPEN).order_by("-cost_impact")[:5]
        )
        if high_cost_risks:
            recommendations.append(
                {
                    "title": "High-cost open risks need mitigation owners",
                    "count": len(high_cost_risks),
                    "details": "Review the highest cost impact open risks and confirm mitigation actions are assigned.",
                }
            )

        # P2 - decision items
        if variations_open_count:
            recommendations.append(
                {
                    "title": "Pending compensation events / variations need decision",
                    "count": variations_open_count,
                    "details": "Approve/reject pending variations and record decision dates where applicable.",
                }
            )
        if early_warnings_open_count:
            recommendations.append(
                {
                    "title": "Open early warnings require close-out action",
                    "count": early_warnings_open_count,
                    "details": "Ensure responses and closure dates are captured for open early warnings.",
                }
            )

        # P3 - housekeeping/quality
        if outstanding_responses.count():
            recommendations.append(
                {
                    "title": "Track outstanding responses and due dates",
                    "count": outstanding_responses.count(),
                    "details": "Capture response due dates for items that require a response to support compliance tracking.",
                }
            )
        if documents_qs.count():
            recommendations.append(
                {
                    "title": "Document register metadata cleanup",
                    "count": documents_qs.count(),
                    "details": "Project documents currently store title/notes only; consider standardizing naming to include revision and issue status in the title/notes until fields are added.",
                }
            )

        # Keep ordering priority-based internally by recomputing a priority per title.
        # (No visible priority labels are shown in the template.)
        priority_lookup = {
            "Overdue responses require escalation": "P1",
            "Delayed milestones impacting programme": "P1",
            "High-cost open risks need mitigation owners": "P1",
            "Pending compensation events / variations need decision": "P2",
            "Open early warnings require close-out action": "P2",
            "Track outstanding responses and due dates": "P3",
            "Document register metadata cleanup": "P3",
        }

        recommendations.sort(
            key=lambda r: (
                _priority_rank(priority_lookup.get(r["title"], "P3")),
                -(r["count"] or 0),
            )
        )

        context["report_overview"] = {
            "open_risks": risks_open_count,
            "closed_risks": risks_closed_count,
            "pending_variations": variations_open_count,
            "closed_variations": variations_closed_count,
            "open_early_warnings": early_warnings_open_count,
            "closed_early_warnings": early_warnings_closed_count,
            "outstanding_responses": outstanding_responses.count(),
            "overdue_outstanding_responses": overdue_outstanding_responses.count(),
            "completed_milestones": milestones_completed_in_period_count,
            "delayed_milestones": len(delayed_milestones),
            "docs_specs_drawings": documents_qs.count(),
        }

        context["key_recommendations"] = {
            "recommendations": recommendations,
        }
        context["month_comparison"] = {
            "risk_register": {
                "current": risks_current_month_count,
                "previous": risks_previous_month_count,
                "diff": risks_current_month_count - risks_previous_month_count,
                "current_open": risks_current_month_open,
                "previous_open": risks_previous_month_open,
                "current_closed": risks_current_month_closed,
                "previous_closed": risks_previous_month_closed,
                "current_cost": risks_current_month_cost,
                "previous_cost": risks_previous_month_cost,
                "diff_cost": risks_current_month_cost - risks_previous_month_cost,
            },
            "variations_register": {
                "current": variations_current_month_count,
                "previous": variations_previous_month_count,
                "diff": variations_current_month_count
                - variations_previous_month_count,
                "current_open": variations_current_month_open,
                "previous_open": variations_previous_month_open,
                "current_closed": variations_current_month_closed,
                "previous_closed": variations_previous_month_closed,
                "current_cost": variations_current_month_cost,
                "previous_cost": variations_previous_month_cost,
                "diff_cost": variations_current_month_cost
                - variations_previous_month_cost,
            },
            "early_warning_register": {
                "current": early_warnings_current_month_count,
                "previous": early_warnings_previous_month_count,
                "diff": early_warnings_current_month_count
                - early_warnings_previous_month_count,
            },
            "drawings_specs": {
                "current": documents_current_month_count,
                "previous": documents_previous_month_count,
                "diff": documents_current_month_count - documents_previous_month_count,
            },
            "communications": {
                "current": correspondences_current_month_count,
                "previous": correspondences_previous_month_count,
                "diff": correspondences_current_month_count
                - correspondences_previous_month_count,
            },
            "programme_extracts": {
                "current": milestones_current_month_count,
                "previous": milestones_previous_month_count,
                "diff": milestones_current_month_count
                - milestones_previous_month_count,
            },
            "current_month_label": current_month_start.strftime("%b %Y"),
            "previous_month_label": previous_month_start.strftime("%b %Y"),
        }

        return context


class ContractorsReportView(ContractualReportMixin, TemplateView):
    """Contractor's report page (initial implementation)."""

    template_name = "project/contractors_report.html"

    def get(self, request, *args, **kwargs):
        export_type = (request.GET.get("export") or "").lower()
        if export_type == "pdf":
            return self._export_pdf()
        return super().get(request, *args, **kwargs)

    def _export_pdf(self) -> HttpResponse:
        context = self.get_context_data()
        project = context["project"]

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 40

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, y, f"Contractor's Report: {project.name}")
        y -= 25
        pdf.setFont("Helvetica", 10)
        pdf.drawString(
            40,
            y,
            f"Period: {context['period_label']} ({context['period_start']} to {context['period_end']})",
        )
        y -= 30

        sections = [
            ("Project Status", context["project_status_summary"]),
            ("Contractor Summary", context["contractor_summary"]),
            (
                "Financial Status",
                f"Contract Value: {context['contract_value']}, Claims this period: {context['financial_summary']['claims_this_period']}",
            ),
            (
                "Health & Safety",
                f"Incidents: {context['incidents_count']}, Near Misses: {context['near_misses_count']}",
            ),
        ]

        for title, text in sections:
            if y < 100:
                pdf.showPage()
                y = height - 40
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(40, y, title)
            y -= 15
            pdf.setFont("Helvetica", 9)
            lines = [str(text)[i : i + 90] for i in range(0, len(str(text)), 90)]
            for line in lines:
                pdf.drawString(50, y, line)
                y -= 12
            y -= 10

        pdf.save()
        data = buffer.getvalue()
        buffer.close()

        filename = f"Contractors_Report_{project.pk}_{context['period_start']}.pdf"
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write(data)
        return response

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title=project.name,
                url=None,
            ),
            BreadcrumbItem(
                title="Contractor's Report",
                url=None,
            ),
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()

        period_key = (self.request.GET.get("period") or "2w").lower()
        period_start, period_end, period_label = (
            ContractualReportView._get_reporting_window(period_key)
        )

        # Calendar period comparison (for 2-week, use previous 2 weeks; for months, use previous month)
        if period_key == "2w":
            current_period_start = period_end - timedelta(days=14)
            current_period_end = period_end
            previous_period_start = current_period_start - timedelta(days=14)
            previous_period_end = current_period_start - timedelta(days=1)
            comparison_label = "2-Week"
        else:
            current_period_start = period_end.replace(day=1)
            current_period_end = (
                current_period_start + relativedelta(months=1) - timedelta(days=1)
            )
            previous_period_start = (
                current_period_start - relativedelta(months=1)
            ).replace(day=1)
            previous_period_end = (
                previous_period_start + relativedelta(months=1) - timedelta(days=1)
            )
            comparison_label = "Month"

        # Get Report Summary for qualitative data
        summary = ProjectReportSummary.objects.filter(
            project=project, period_start__lte=period_end, period_end__gte=period_start
        ).first()

        consultants = project.lead_consultants.all()
        client = project.client.name if project.client else "-"
        contractor = project.contractor.name if project.contractor else "-"

        milestones = Milestone.objects.filter(project=project).order_by(
            "planned_date", "sequence"
        )
        milestones_achieved = milestones.filter(
            actual_date__range=(period_start, period_end)
        )
        upcoming_milestones = milestones.filter(planned_date__gt=period_end)[:10]
        delayed_milestones = [m for m in milestones if m.is_delayed]

        # Window-specific risks for reporting section
        risks = Risk.objects.filter(
            project=project, date__range=(period_start, period_end)
        ).select_related("raised_by")
        open_risks = risks.filter(status=RiskStatus.OPEN)
        closed_risks = risks.filter(status=RiskStatus.CLOSED)

        # All open risks (not period-filtered) for dashboard
        all_open_risks = Risk.objects.filter(
            project=project, status=RiskStatus.OPEN
        ).select_related("raised_by")

        variations = ContractVariation.objects.filter(
            project=project,
            date_identified__isnull=False,
            date_identified__range=(period_start, period_end),
        )
        all_variations = ContractVariation.objects.filter(
            project=project,
            date_identified__isnull=False,
        )
        pending_variations = variations.exclude(
            status__in=[
                ContractVariation.Status.APPROVED,
                ContractVariation.Status.REJECTED,
            ]
        )
        all_pending_variations = all_variations.exclude(
            status__in=[
                ContractVariation.Status.APPROVED,
                ContractVariation.Status.REJECTED,
            ]
        )

        early_warnings = EarlyWarning.objects.filter(
            project=project, date__range=(period_start, period_end)
        )
        open_early_warnings = early_warnings.filter(status=EarlyWarningStatus.OPEN)

        correspondences = ContractualCorrespondence.objects.filter(
            project=project,
            date_of_correspondence__range=(period_start, period_end),
            deleted=False,
        )
        instructions = correspondences.filter(
            correspondence_type=ContractualCorrespondence.CorrespondenceType.INSTRUCTION
        )
        outstanding_responses = correspondences.filter(
            requires_response=True, response_sent=False
        )

        overall_status = "On schedule"
        if delayed_milestones:
            overall_status = "Behind schedule"
        elif milestones_achieved.exists() and not delayed_milestones:
            overall_status = "Ahead / on schedule"

        contract_value = getattr(project, "contract_value", None) or 0
        claims_value = sum((v.variation_amount or 0) for v in variations)
        all_claims_value = sum((v.variation_amount or 0) for v in all_variations)

        latest_forecast = (
            project.forecasts.filter(
                status=Forecast.Status.APPROVED, period__lte=period_end
            )
            .order_by("-period")
            .first()
        )
        forecast_to_completion = (
            latest_forecast.total_forecast if latest_forecast else "-"
        )

        # Get project actual completion/actual end date
        project_actual_end = getattr(project, "actual_end_date", None) or "-"

        # Period comparison data
        risks_current = Risk.objects.filter(
            project=project, date__range=(current_period_start, current_period_end)
        ).count()
        risks_previous = Risk.objects.filter(
            project=project, date__range=(previous_period_start, previous_period_end)
        ).count()
        risks_current_open = Risk.objects.filter(
            project=project,
            date__range=(current_period_start, current_period_end),
            status=RiskStatus.OPEN,
        ).count()
        risks_previous_open = Risk.objects.filter(
            project=project,
            date__range=(previous_period_start, previous_period_end),
            status=RiskStatus.OPEN,
        ).count()
        risk_cost_current = (
            Risk.objects.filter(
                project=project, date__range=(current_period_start, current_period_end)
            )
            .aggregate(total=Sum("cost_impact"))
            .get("total")
            or 0
        )
        risk_cost_previous = (
            Risk.objects.filter(
                project=project,
                date__range=(previous_period_start, previous_period_end),
            )
            .aggregate(total=Sum("cost_impact"))
            .get("total")
            or 0
        )

        variations_current = ContractVariation.objects.filter(
            project=project,
            date_identified__range=(current_period_start, current_period_end),
            date_identified__isnull=False,
        ).count()
        variations_previous = ContractVariation.objects.filter(
            project=project,
            date_identified__range=(previous_period_start, previous_period_end),
            date_identified__isnull=False,
        ).count()
        variations_current_cost = (
            ContractVariation.objects.filter(
                project=project,
                date_identified__range=(current_period_start, current_period_end),
                date_identified__isnull=False,
            )
            .aggregate(total=Sum("variation_amount"))
            .get("total")
            or 0
        )
        variations_previous_cost = (
            ContractVariation.objects.filter(
                project=project,
                date_identified__range=(previous_period_start, previous_period_end),
                date_identified__isnull=False,
            )
            .aggregate(total=Sum("variation_amount"))
            .get("total")
            or 0
        )

        # ── Bi-weekly reports (Safety / Quality) ─────────────────────
        biweekly_safety = (
            BiWeeklySafetyReport.objects.filter(
                project=project,
                period_start__lte=period_end,
                period_end__gte=period_start,
            )
            .order_by("-period_end", "-created_at")
            .first()
        )
        biweekly_quality = (
            BiWeeklyQualityReport.objects.filter(
                project=project,
                period_start__lte=period_end,
                period_end__gte=period_start,
            )
            .prefetch_related(
                "activity_inspections",
                "material_deliveries",
                "workmanship_records",
                "site_audits",
            )
            .order_by("-period_end", "-created_at")
            .first()
        )

        # ── Progress & Resources (from Site Management logs) ─────────
        progress_trackers = ProgressTracker.objects.filter(project=project).order_by(
            "planned_start_date", "activity"
        )
        progress_trackers_in_window = [
            p
            for p in progress_trackers
            if not (
                p.planned_end_date < period_start or p.planned_start_date > period_end
            )
        ][:50]

        def _planned_pct(p: ProgressTracker) -> float:
            # Planned % is derived from planned dates vs period_end (simple and predictable)
            if period_end < p.planned_start_date:
                return 0.0
            if period_end >= p.planned_end_date:
                return 100.0
            total_days = max((p.planned_end_date - p.planned_start_date).days, 1)
            elapsed_days = max((period_end - p.planned_start_date).days, 0)
            return min(100.0, max(0.0, (elapsed_days / total_days) * 100.0))

        progress_rows = []
        for p in progress_trackers_in_window:
            planned = _planned_pct(p)
            actual = float(p.completion_percentage or 0)
            progress_rows.append(
                {
                    "activity": p.activity,
                    "milestone": (p.milestone.name if p.milestone else "-"),
                    "planned_start": p.planned_start_date,
                    "planned_end": p.planned_end_date,
                    "planned_pct": planned,
                    "actual_pct": actual,
                    "variance_pct": actual - planned,
                    "impact": p.impact_description or "On track",
                    "remarks": p.remarks,
                }
            )

        labour_qs = LabourLog.objects.filter(
            project=project, date__range=(period_start, period_end)
        )
        labour_hours = labour_qs.aggregate(total=Sum("hours_worked"))["total"] or 0
        labour_people = labour_qs.values("id_number").distinct().count()

        plant_qs = PlantEquipment.objects.filter(
            project=project, date__range=(period_start, period_end)
        )
        plant_hours = plant_qs.aggregate(total=Sum("usage_hours"))["total"] or 0
        plant_breakdowns = plant_qs.filter(
            breakdown_status=PlantEquipment.BreakdownStatus.BREAKDOWN
        ).count()

        materials_qs = MaterialsLog.objects.filter(
            project=project, date_received__range=(period_start, period_end)
        )
        materials_total_qty = (
            materials_qs.aggregate(total=Sum("quantity"))["total"] or 0
        )
        materials_units = list(
            materials_qs.values_list("unit", flat=True).distinct()[:5]
        )
        materials_unit_label = (
            materials_units[0] if len(materials_units) == 1 else "mixed"
        )

        productivity_qs = ProductivityLog.objects.filter(
            project=project, date__range=(period_start, period_end)
        )
        productivity_outputs = productivity_qs.count()

        # ── Safety: Incidents & Near-Misses ──────────────────────────
        all_incidents = Incident.objects.filter(
            project=project, date__range=(period_start, period_end)
        ).select_related("reported_by")
        site_incidents = all_incidents.filter(incident_type=IncidentType.INCIDENT)
        near_misses = all_incidents.filter(incident_type=IncidentType.NEAR_MISS)

        # ── Safety NCRs ──────────────────────────────────────────────
        safety_ncrs = NonConformance.objects.filter(
            project=project,
            ncr_type=NCRType.SAFETY,
            date__range=(period_start, period_end),
        ).select_related("responsible_person")
        safety_ncrs_open = safety_ncrs.filter(status=NCRStatus.OPEN)
        safety_ncrs_closed = safety_ncrs.filter(status=NCRStatus.CLOSED)

        # ── Quality NCRs ─────────────────────────────────────────────
        quality_ncrs = NonConformance.objects.filter(
            project=project,
            ncr_type=NCRType.QUALITY,
            date__range=(period_start, period_end),
        ).select_related("responsible_person")
        quality_ncrs_open = quality_ncrs.filter(status=NCRStatus.OPEN)
        quality_ncrs_closed = quality_ncrs.filter(status=NCRStatus.CLOSED)

        # ── QC inspections (existing QualityControl model) ───────────
        qc_records = QualityControl.objects.filter(
            project=project, date__range=(period_start, period_end)
        )

        # Determine dynamic summaries from ProjectReportSummary
        status_summary = (
            summary.project_status_summary
            if summary and summary.project_status_summary
            else f"Works are {overall_status}. {milestones_achieved.count()} milestones achieved."
        )
        contractor_summary = (
            summary.contractor_summary
            if summary and summary.contractor_summary
            else "Contractor's periodic progress update and key highlights."
        )

        context.update(
            {
                "project": project,
                "tab": "contractors_report",
                "period_key": period_key,
                "period_label": period_label,
                "comparison_label": comparison_label,
                "period_start": period_start,
                "period_end": period_end,
                "client": client,
                "contractor": contractor,
                "contract_reference": project.contract_number or "-",
                "contract_value": contract_value,
                "consultants": ", ".join(
                    [(c.get_full_name() or c.email or str(c.pk)) for c in consultants]
                ),
                "overall_status": overall_status,
                "project_status_summary": status_summary,
                "contractor_summary": contractor_summary,
                "milestones_achieved": milestones_achieved,
                "upcoming_milestones": upcoming_milestones,
                "delayed_milestones": delayed_milestones,
                "open_risks": open_risks,
                "all_open_risks": all_open_risks,
                "closed_risks_count": closed_risks.count(),
                "open_risks_count": open_risks.count(),
                "all_open_risks_count": all_open_risks.count(),
                "total_risks_count": risks.count(),
                "early_warnings": early_warnings,
                "open_early_warnings_count": open_early_warnings.count(),
                "variations": variations,
                "all_variations": all_variations,
                "pending_variations": pending_variations,
                "all_pending_variations": all_pending_variations,
                "instructions": instructions,
                "outstanding_responses": outstanding_responses,
                "forecast_to_completion": forecast_to_completion,
                "project_actual_end": project_actual_end,
                "progress_rows": progress_rows,
                "resources_rows": [
                    {
                        "resource": "Labour",
                        "planned": "-",
                        "actual": f"{labour_people} people / {labour_hours} hours",
                        "variance": "-",
                        "comments": f"{labour_qs.count()} log entries (plus {productivity_outputs} productivity entries)",
                    },
                    {
                        "resource": "Plant/Equipment",
                        "planned": "-",
                        "actual": f"{plant_qs.count()} items / {plant_hours} hours",
                        "variance": "-",
                        "comments": f"{plant_breakdowns} breakdown entries",
                    },
                    {
                        "resource": "Materials",
                        "planned": "-",
                        "actual": f"{materials_total_qty} {materials_unit_label}",
                        "variance": "-",
                        "comments": f"{materials_qs.count()} deliveries",
                    },
                ],
                # Period comparison
                "period_comparison": {
                    "risk_register": {
                        "current": risks_current,
                        "previous": risks_previous,
                        "diff": risks_current - risks_previous,
                        "current_open": risks_current_open,
                        "previous_open": risks_previous_open,
                        "current_cost": risk_cost_current,
                        "previous_cost": risk_cost_previous,
                        "diff_cost": risk_cost_current - risk_cost_previous,
                    },
                    "variations_register": {
                        "current": variations_current,
                        "previous": variations_previous,
                        "diff": variations_current - variations_previous,
                        "current_cost": variations_current_cost,
                        "previous_cost": variations_previous_cost,
                        "diff_cost": variations_current_cost - variations_previous_cost,
                    },
                    "current_period_label": f"{current_period_start.strftime('%b %d')} - {current_period_end.strftime('%b %d, %Y')}",
                    "previous_period_label": f"{previous_period_start.strftime('%b %d')} - {previous_period_end.strftime('%b %d, %Y')}",
                },
                # Financial summary
                "financial_summary": {
                    "contract_value": contract_value,
                    "claims_this_period": claims_value,
                    "all_variants_total": all_claims_value,
                    "variations_count": all_variations.count(),
                    "pending_count": all_pending_variations.count(),
                    "approved_count": all_variations.filter(
                        status=ContractVariation.Status.APPROVED
                    ).count(),
                    "rejected_count": all_variations.filter(
                        status=ContractVariation.Status.REJECTED
                    ).count(),
                    "forecast_completion": forecast_to_completion,
                    "actual_completion": project_actual_end,
                },
                # Safety
                "site_incidents": site_incidents,
                "near_misses": near_misses,
                "incidents_count": site_incidents.count(),
                "near_misses_count": near_misses.count(),
                "safety_ncrs": safety_ncrs,
                "safety_ncrs_open": safety_ncrs_open,
                "safety_ncrs_closed": safety_ncrs_closed,
                "safety_ncrs_open_count": safety_ncrs_open.count(),
                "safety_ncrs_closed_count": safety_ncrs_closed.count(),
                "biweekly_safety": biweekly_safety,
                # Quality
                "quality_ncrs": quality_ncrs,
                "quality_ncrs_open": quality_ncrs_open,
                "quality_ncrs_closed": quality_ncrs_closed,
                "quality_ncrs_open_count": quality_ncrs_open.count(),
                "quality_ncrs_closed_count": quality_ncrs_closed.count(),
                "qc_records": qc_records,
                "biweekly_quality": biweekly_quality,
                # Appendices
                "appendix_groups": [
                    {
                        "title": "Contractual Registers",
                        "links": [
                            {
                                "label": "Detailed Risk Register",
                                "url": reverse("project:risk-list", args=[project.pk]),
                            },
                            {
                                "label": "Detailed CE / Variations Register",
                                "url": reverse(
                                    "bill_of_quantities:variation-list",
                                    args=[project.pk],
                                ),
                            },
                            {
                                "label": "Detailed Early Warning Register",
                                "url": reverse(
                                    "site_management:early-warning-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Supporting Correspondence",
                                "url": reverse(
                                    "bill_of_quantities:correspondence-list",
                                    args=[project.pk],
                                ),
                            },
                        ],
                    },
                    {
                        "title": "Site Management Registers",
                        "links": [
                            {
                                "label": "Site Management Home",
                                "url": reverse(
                                    "site_management:site-management",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Progress Tracker",
                                "url": reverse(
                                    "site_management:progress-tracker-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Bi-Weekly Safety Reports",
                                "url": reverse(
                                    "site_management:biweekly-safety-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Bi-Weekly Quality Reports",
                                "url": reverse(
                                    "site_management:biweekly-quality-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Quality Control Register",
                                "url": reverse(
                                    "site_management:quality-control-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Safety Observations",
                                "url": reverse(
                                    "site_management:safety-observation-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Site Instructions",
                                "url": reverse(
                                    "site_management:site-instruction-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "RFIs",
                                "url": reverse(
                                    "site_management:rfi-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Meetings",
                                "url": reverse(
                                    "site_management:meeting-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Daily Diary",
                                "url": reverse(
                                    "site_management:daily-diary-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Delays Log",
                                "url": reverse(
                                    "site_management:delay-log-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Photo Log",
                                "url": reverse(
                                    "site_management:photo-log-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Procurement Tracker",
                                "url": reverse(
                                    "site_management:procurement-tracker-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Delivery Tracker",
                                "url": reverse(
                                    "site_management:delivery-tracker-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Off-Site Log",
                                "url": reverse(
                                    "site_management:offsite-log-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Subcontractor Log",
                                "url": reverse(
                                    "site_management:subcontractor-log-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Snag List",
                                "url": reverse(
                                    "site_management:snag-list-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                        ],
                    },
                    {
                        "title": "Resources (Logs)",
                        "links": [
                            {
                                "label": "Labour Log",
                                "url": reverse(
                                    "site_management:labour-log-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Plant & Equipment",
                                "url": reverse(
                                    "site_management:plant-equipment-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Materials Log",
                                "url": reverse(
                                    "site_management:materials-log-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                            {
                                "label": "Productivity Log",
                                "url": reverse(
                                    "site_management:productivity-log-list",
                                    kwargs={"project_pk": project.pk},
                                ),
                            },
                        ],
                    },
                ],
            }
        )
        return context


class ConstructionProgressReportView(ContractualReportMixin, TemplateView):
    """Construction Progress Report - PM perspective for client communication."""

    template_name = "project/construction_progress_report.html"

    def get(self, request, *args, **kwargs):
        export_type = (request.GET.get("export") or "").lower()
        if export_type == "pdf":
            return self._export_pdf()
        return super().get(request, *args, **kwargs)

    def _export_pdf(self) -> HttpResponse:
        context = self.get_context_data()
        project = context["project"]

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 40

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, y, f"Construction Progress Report: {project.name}")
        y -= 25
        pdf.setFont("Helvetica", 10)
        pdf.drawString(
            40,
            y,
            f"Period: {context['period_label']} ({context['period_start']} to {context['period_end']})",
        )
        y -= 30

        sections = [
            ("Project Status", context["project_status_summary"]),
            ("Key Achievements", context["key_achievements_text"]),
            ("Current Focus", context["current_focus_text"]),
            ("Financial Summary", context["financial_summary_text"]),
            ("HSQ Summary", context["hsq_summary_text"]),
            ("Recommendations", context["recommendations_text"]),
        ]

        for title, text in sections:
            if y < 100:
                pdf.showPage()
                y = height - 40
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(40, y, title)
            y -= 15
            pdf.setFont("Helvetica", 9)
            # Simple text wrapping for PDF
            lines = [text[i : i + 90] for i in range(0, len(text), 90)]
            for line in lines:
                pdf.drawString(50, y, line)
                y -= 12
            y -= 10

        pdf.save()
        data = buffer.getvalue()
        buffer.close()

        filename = f"Progress_Report_{project.pk}_{context['period_start']}.pdf"
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write(data)
        return response

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title=project.name,
                url=None,
            ),
            BreadcrumbItem(
                title="Construction Progress Report",
                url=None,
            ),
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        from django.utils import timezone

        context = super().get_context_data(**kwargs)
        project = self.get_project()

        period_key = (self.request.GET.get("period") or "2w").lower()
        period_start, period_end, period_label = (
            ContractualReportView._get_reporting_window(period_key)
        )

        # Get Report Summary for qualitative data
        summary = ProjectReportSummary.objects.filter(
            project=project, period_start__lte=period_end, period_end__gte=period_start
        ).first()

        # ── Project Information ──────────────────────────────────────
        client = project.client.name if project.client else "-"
        contractor = project.contractor.name if project.contractor else "-"
        project_manager = (
            f"{project.project_manager.get_full_name()}"
            if hasattr(project, "project_manager") and project.project_manager
            else "TBD"
        )

        # ── Milestones ───────────────────────────────────────────────
        all_milestones = Milestone.objects.filter(project=project).order_by(
            "planned_date", "sequence"
        )
        milestones_achieved = all_milestones.filter(
            actual_date__range=(period_start, period_end)
        )
        milestones_in_progress = all_milestones.filter(
            actual_date__isnull=True,
            forecast_date__lte=period_end,
        )
        milestones_upcoming = all_milestones.filter(planned_date__gt=period_end)
        delayed_milestones = [m for m in all_milestones if m.is_delayed]

        # ── Schedule Status ──────────────────────────────────────────
        total_milestones = all_milestones.count()
        completed_milestones = all_milestones.filter(actual_date__isnull=False).count()
        overall_progress_pct = (
            Decimal(completed_milestones) / Decimal(total_milestones) * Decimal("100")
            if total_milestones > 0
            else Decimal("0")
        )
        planned_milestones = all_milestones.filter(planned_date__lte=period_end).count()
        planned_progress_pct = (
            Decimal(planned_milestones) / Decimal(total_milestones) * Decimal("100")
            if total_milestones > 0
            else Decimal("0")
        )
        actual_progress_pct = overall_progress_pct

        original_end_date = project.end_date
        forecast_end_date = (
            max(
                [m.forecast_date for m in all_milestones if m.forecast_date],
                default=original_end_date,
            )
            if original_end_date
            else None
        )
        schedule_variance_days = (
            (forecast_end_date - original_end_date).days
            if forecast_end_date and original_end_date
            else 0
        )
        schedule_status = (
            "On Track"
            if schedule_variance_days <= 0
            else ("At Risk" if schedule_variance_days <= 7 else "Behind Schedule")
        )

        # ── Progress Tracking ────────────────────────────────────────
        progress_trackers = ProgressTracker.objects.filter(project=project).order_by(
            "planned_start_date"
        )
        completed_activities = progress_trackers.filter(
            completion_percentage=100, actual_end_date__range=(period_start, period_end)
        )
        upcoming_activities = progress_trackers.filter(
            planned_start_date__gt=period_end
        )[:10]

        # ── Financial Status ─────────────────────────────────────────
        contract_value = project.total_contract_value
        # Real spent to date from project model
        spent_to_date = project.get_actual_cost(period_end)
        remaining_budget = contract_value - spent_to_date
        budget_spend_pct = (
            (spent_to_date / contract_value * 100) if contract_value else Decimal("0")
        )

        all_variations = ContractVariation.objects.filter(
            project=project, date_identified__isnull=False
        )
        total_variations = sum((v.variation_amount or 0) for v in all_variations)
        forecast_at_completion = contract_value + total_variations

        # Real CPI/SPI from project model
        cpi = project.get_cost_performance_index(period_end) or Decimal("1.0")
        spi = project.get_schedule_performance_index(period_end) or Decimal("1.0")

        forecast_status = (
            "On Track"
            if cpi >= 0.95
            and spent_to_date <= (budget_spend_pct / 100) * contract_value
            else ("At Risk" if cpi >= 0.90 else "Over Budget")
        )

        # ── Risks ────────────────────────────────────────────────────
        all_open_risks = Risk.objects.filter(
            project=project, status=RiskStatus.OPEN
        ).select_related("raised_by")
        critical_risks_count = all_open_risks.filter(cost_impact__gte=500000).count()
        high_risks_count = (
            all_open_risks.filter(cost_impact__gte=100000)
            .exclude(cost_impact__gte=500000)
            .count()
        )
        top_open_risks = all_open_risks.order_by("-cost_impact")[:5]

        # ── Safety & Quality ─────────────────────────────────────────
        site_incidents = Incident.objects.filter(
            project=project,
            incident_type=IncidentType.INCIDENT,
            date__range=(period_start, period_end),
        )
        near_misses = Incident.objects.filter(
            project=project,
            incident_type=IncidentType.NEAR_MISS,
            date__range=(period_start, period_end),
        )
        safety_ncrs = NonConformance.objects.filter(
            project=project,
            ncr_type=NCRType.SAFETY,
            date__range=(period_start, period_end),
        )
        safety_ncrs_open = safety_ncrs.filter(status=NCRStatus.OPEN)

        quality_ncrs = NonConformance.objects.filter(
            project=project,
            ncr_type=NCRType.QUALITY,
            date__range=(period_start, period_end),
        )
        quality_ncrs_open = quality_ncrs.filter(status=NCRStatus.OPEN)

        qc_records = QualityControl.objects.filter(
            project=project, date__range=(period_start, period_end)
        )
        qc_passed = qc_records.filter(result="PASS")

        # Determine dynamic summaries from ProjectReportSummary
        status_summary = (
            summary.project_status_summary
            if summary and summary.project_status_summary
            else f"Works are {overall_progress_pct:.1f}% complete. {schedule_status}."
        )
        achievements_text = (
            summary.key_achievements
            if summary and summary.key_achievements
            else f"Completed {milestones_achieved.count()} milestone(s) and {completed_activities.count()} activity(ies) this period."
        )
        focus_text = (
            summary.current_focus
            if summary and summary.current_focus
            else f"Working on {milestones_in_progress.count()} milestone(s) and {upcoming_activities.count()} upcoming activity(ies)."
        )
        hsq_summary_text = (
            summary.hsq_summary
            if summary and summary.hsq_summary
            else f"{site_incidents.count()} incident(s), {near_misses.count()} near miss(es) this period. Quality pass rate: {(qc_passed.count() / qc_records.count() * 100) if qc_records.count() else 100:.1f}%."
        )
        recommendations_text = (
            summary.recommendations
            if summary and summary.recommendations
            else "Continue current work plan. Monitor schedule and budget."
        )

        context.update(
            {
                "project": project,
                "tab": "progress_report",
                "period_key": period_key,
                "period_label": period_label,
                "period_start": period_start,
                "period_end": period_end,
                "report_date": timezone.now().date(),
                "client": client,
                "contractor": contractor,
                "contract_reference": project.contract_number or "-",
                "project_manager": project_manager,
                # Executive Summary
                "overall_progress_pct": overall_progress_pct,
                "schedule_status": schedule_status,
                "milestones_achieved": milestones_achieved,
                "project_status_summary": status_summary,
                "key_achievements_text": achievements_text,
                "current_focus_text": focus_text,
                "major_risks_summary": f"{critical_risks_count} critical risk(s), {high_risks_count} high risk(s).",
                # Milestones
                "all_milestones": all_milestones,
                "milestones_in_progress": milestones_in_progress,
                "milestones_upcoming": milestones_upcoming,
                "delayed_milestones": delayed_milestones,
                # Work Completed/Planned
                "work_completed_summary": (
                    f"{completed_activities.count()} activities completed this period. "
                    f"{milestones_achieved.count()} milestone(s) were achieved."
                ),
                "completed_activities": [
                    {
                        "activity": a.activity,
                        "actual_pct": 100,
                        "actual_end_date": a.actual_end_date,
                        "impact": a.impact_description or "Positive",
                    }
                    for a in completed_activities[:10]
                ],
                "work_planned_summary": (
                    "Next planned work: "
                    + (
                        "; ".join(
                            f"{a.activity} ({a.planned_start_date:%Y-%m-%d} to {a.planned_end_date:%Y-%m-%d})"
                            for a in upcoming_activities[:3]
                        )
                        if upcoming_activities
                        else "No planned activities recorded for the next period."
                    )
                ),
                "upcoming_activities": [
                    {
                        "name": a.activity,
                        "start_date": a.planned_start_date,
                        "end_date": a.planned_end_date,
                        "duration_days": (
                            (a.planned_end_date - a.planned_start_date).days
                            if a.planned_end_date and a.planned_start_date
                            else 0
                        ),
                        "priority": "HIGH",
                    }
                    for a in upcoming_activities
                ],
                # Schedule
                "original_end_date": original_end_date,
                "forecast_end_date": forecast_end_date or original_end_date,
                "schedule_variance_days": schedule_variance_days,
                "planned_progress_pct": planned_progress_pct,
                "actual_progress_pct": actual_progress_pct,
                "schedule_status_text": f"Project is {schedule_status}.",
                # Financial
                "financial_status": {
                    "contract_value": int(contract_value),
                    "spent_to_date": int(spent_to_date),
                    "remaining_budget": int(remaining_budget),
                    "budget_spend_pct": budget_spend_pct,
                    "forecast_at_completion": int(forecast_at_completion),
                    "total_variations": int(total_variations),
                    "cpi": cpi,
                    "spi": spi,
                    "forecast_status": forecast_status,
                },
                "financial_summary_text": f"Contract: {contract_value:,}. Spent: {spent_to_date:,}. Forecast: {forecast_at_completion:,}",
                # Risks
                "critical_risks_count": critical_risks_count,
                "high_risks_count": high_risks_count,
                "all_open_risks_count": all_open_risks.count(),
                "top_open_risks": top_open_risks,
                # Safety & Quality
                "incidents_count": site_incidents.count(),
                "near_misses_count": near_misses.count(),
                "safety_ncrs_open_count": safety_ncrs_open.count(),
                "qc_records_count": qc_records.count(),
                "qc_passed_count": qc_passed.count(),
                "quality_ncrs_open_count": quality_ncrs_open.count(),
                "hsq_summary_text": hsq_summary_text,
                # Next Steps
                "recommendations_text": recommendations_text,
            }
        )

        return context


class ComplianceReportView(ContractualReportView):
    """Comprehensive Project Compliance Report (Contractual, Administrative, Final Account, Quality, Safety, etc.)."""

    template_name = "project/compliance_report.html"

    def get(self, request, *args, **kwargs):
        export_type = (request.GET.get("export") or "").lower()
        register = (request.GET.get("register") or "").lower()
        if export_type == "csv" and register:
            return self._export_register_csv(register)
        if export_type == "pdf" and register:
            return self._export_register_pdf(register)
        return super().get(request, *args, **kwargs)

    def _build_register_export_data(
        self, register: str
    ) -> tuple[list[str], list[list[Any]], str] | None:
        project = self.get_project()
        period_key = (self.request.GET.get("period") or "1m").lower()
        period_start, period_end, _ = self._get_reporting_window(period_key)

        rows: list[list[Any]] = []
        headers: list[str] = []
        filename = f"{register}_{project.pk}_{period_start}_{period_end}"

        if register == "contractual":
            headers = [
                "ID",
                "Obligation",
                "Responsible Party",
                "Contract Reference",
                "Due Date",
                "Status",
                "Notes",
            ]
            queryset = ContractualCompliance.objects.filter(
                project=project, deleted=False
            ).filter(due_date__range=(period_start, period_end))
            for item in queryset:
                responsible = "-"
                if item.responsible_party:
                    responsible = (
                        item.responsible_party.get_full_name()
                        or item.responsible_party.email
                    )
                rows.append(
                    [
                        f"CC-{item.pk}",
                        item.obligation_description,
                        responsible,
                        item.contract_reference,
                        item.due_date.isoformat() if item.due_date else "",
                        item.get_status_display(),
                        item.notes,
                    ]
                )
        elif register == "administrative":
            headers = [
                "ID",
                "Type",
                "Reference",
                "Description",
                "Responsible Party",
                "Submission Due",
                "Submission Date",
                "Approval Due",
                "Approval Date",
                "Status",
            ]
            queryset = AdministrativeCompliance.objects.filter(
                project=project, deleted=False
            ).filter(
                Q(submission_due_date__range=(period_start, period_end))
                | Q(approval_due_date__range=(period_start, period_end))
            )
            for item in queryset:
                responsible = "-"
                if item.responsible_party:
                    responsible = (
                        item.responsible_party.get_full_name()
                        or item.responsible_party.email
                    )
                rows.append(
                    [
                        f"AC-{item.pk}",
                        item.get_item_type_display(),
                        item.reference_number,
                        item.description,
                        responsible,
                        item.submission_due_date.isoformat()
                        if item.submission_due_date
                        else "",
                        item.submission_date.isoformat()
                        if item.submission_date
                        else "",
                        item.approval_due_date.isoformat()
                        if item.approval_due_date
                        else "",
                        item.approval_date.isoformat() if item.approval_date else "",
                        item.get_status_display(),
                    ]
                )
        elif register == "final_account":
            headers = [
                "ID",
                "Document Type",
                "Description",
                "Responsible Party",
                "Submission Date",
                "Approval Date",
                "Status",
                "Notes",
            ]
            queryset = FinalAccountCompliance.objects.filter(
                project=project, deleted=False
            ).filter(
                Q(submission_date__range=(period_start, period_end))
                | Q(approval_date__range=(period_start, period_end))
            )
            for item in queryset:
                responsible = "-"
                if item.responsible_party:
                    responsible = (
                        item.responsible_party.get_full_name()
                        or item.responsible_party.email
                    )
                rows.append(
                    [
                        f"FA-{item.pk}",
                        item.get_document_type_display(),
                        item.description,
                        responsible,
                        item.submission_date.isoformat()
                        if item.submission_date
                        else "",
                        item.approval_date.isoformat() if item.approval_date else "",
                        item.get_status_display(),
                        item.notes,
                    ]
                )
        elif register == "ncr":
            headers = [
                "NCR No.",
                "Description",
                "Date",
                "Category",
                "Severity",
                "Status",
                "Responsible Party",
                "Due Date",
                "Closed Date",
            ]
            queryset = NonConformance.objects.filter(
                project=project, date__range=(period_start, period_end)
            )
            for ncr in queryset:
                responsible = "-"
                if ncr.responsible_party:
                    responsible = (
                        ncr.responsible_party.get_full_name()
                        or ncr.responsible_party.email
                    )
                rows.append(
                    [
                        ncr.reference_number,
                        ncr.description,
                        ncr.date.isoformat() if ncr.date else "",
                        ncr.get_ncr_type_display(),
                        ncr.get_status_display(),
                        ncr.get_status_display(),
                        responsible,
                        "",  # NonConformance doesn't have a due_date field in the choices provided earlier
                        ncr.date_closed.isoformat() if ncr.date_closed else "",
                    ]
                )
        elif register == "incidents":
            headers = [
                "Incident No.",
                "Description",
                "Date",
                "Type",
                "Severity",
                "Status",
                "Reported By",
                "Investigation Due",
                "Closed Date",
            ]
            queryset = Incident.objects.filter(
                project=project, date__range=(period_start, period_end)
            )
            for incident in queryset:
                reported_by = "-"
                if incident.reported_by:
                    reported_by = (
                        incident.reported_by.get_full_name()
                        or incident.reported_by.email
                    )
                rows.append(
                    [
                        incident.reference_number,
                        incident.description,
                        incident.date.isoformat() if incident.date else "",
                        incident.get_type_display(),
                        incident.get_severity_display(),
                        incident.get_status_display(),
                        reported_by,
                        incident.investigation_due_date.isoformat()
                        if incident.investigation_due_date
                        else "",
                        incident.date_closed.isoformat()
                        if incident.date_closed
                        else "",
                    ]
                )
        elif register == "early_warnings":
            headers = [
                "EW No.",
                "Subject",
                "Raised By",
                "Date",
                "Status",
                "Response",
            ]
            queryset = EarlyWarning.objects.filter(
                project=project, date__range=(period_start, period_end)
            )
            for ew in queryset:
                raised_by = "-"
                if ew.submitted_by:
                    raised_by = ew.submitted_by.get_full_name() or ew.submitted_by.email
                rows.append(
                    [
                        ew.reference_number,
                        ew.subject,
                        raised_by,
                        ew.date.isoformat() if ew.date else "",
                        ew.get_status_display(),
                        ew.response or "",
                    ]
                )
        elif register == "quality_reports":
            headers = [
                "Period Start",
                "Period End",
                "Submitted By",
                "Notes",
            ]
            queryset = BiWeeklyQualityReport.objects.filter(
                project=project, period_end__range=(period_start, period_end)
            )
            for report in queryset:
                submitted_by = "-"
                if report.submitted_by:
                    submitted_by = (
                        report.submitted_by.get_full_name() or report.submitted_by.email
                    )
                rows.append(
                    [
                        report.period_start.isoformat() if report.period_start else "",
                        report.period_end.isoformat() if report.period_end else "",
                        submitted_by,
                        report.notes or "",
                    ]
                )
        elif register == "safety_reports":
            headers = [
                "Period Start",
                "Period End",
                "Submitted By",
                "Key Concerns",
                "Notes",
            ]
            queryset = BiWeeklySafetyReport.objects.filter(
                project=project, period_end__range=(period_start, period_end)
            )
            for report in queryset:
                submitted_by = "-"
                if report.submitted_by:
                    submitted_by = (
                        report.submitted_by.get_full_name() or report.submitted_by.email
                    )
                rows.append(
                    [
                        report.period_start.isoformat() if report.period_start else "",
                        report.period_end.isoformat() if report.period_end else "",
                        submitted_by,
                        report.key_concerns or "",
                        report.notes or "",
                    ]
                )
        elif register == "rfis":
            headers = [
                "RFI No.",
                "Subject",
                "Issued Date",
                "Status",
                "Response Date",
                "Days to Respond",
            ]
            queryset = RFI.objects.filter(
                project=project, date_issued__range=(period_start, period_end)
            )
            for rfi in queryset:
                days_to_respond = None
                if rfi.date_issued and rfi.response_date:
                    days_to_respond = (rfi.response_date - rfi.date_issued).days
                rows.append(
                    [
                        rfi.reference_number,
                        rfi.subject,
                        rfi.date_issued.isoformat() if rfi.date_issued else "",
                        rfi.get_status_display(),
                        rfi.response_date.isoformat() if rfi.response_date else "",
                        days_to_respond,
                    ]
                )
        elif register == "site_instructions":
            headers = [
                "SI No.",
                "Subject",
                "Notified Date",
                "Status",
                "Closed Date",
                "Days to Close",
            ]
            queryset = SiteInstruction.objects.filter(
                project=project, date_notified__range=(period_start, period_end)
            )
            for si in queryset:
                days_to_close = None
                if si.date_notified and si.date_closed:
                    days_to_close = (si.date_closed - si.date_notified).days
                rows.append(
                    [
                        si.reference_number,
                        si.subject,
                        si.date_notified.isoformat() if si.date_notified else "",
                        si.get_status_display(),
                        si.date_closed.isoformat() if si.date_closed else "",
                        days_to_close,
                    ]
                )
        else:
            return None

        return headers, rows, filename

    def _export_register_csv(self, register: str) -> HttpResponse:
        export_data = self._build_register_export_data(register)
        if export_data is None:
            return HttpResponse(status=400)
        headers, rows, filename = export_data

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(rows)
        return response

    def _export_register_pdf(self, register: str) -> HttpResponse:
        export_data = self._build_register_export_data(register)
        if export_data is None:
            return HttpResponse(status=400)
        headers, rows, filename = export_data

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 40

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(40, y, f"{register.title().replace('_', ' ')} Register Export")
        y -= 18
        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, " | ".join(headers))
        y -= 14
        pdf.line(40, y, width - 40, y)
        y -= 12

        for row in rows:
            if y < 40:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica", 9)
            row_text = " | ".join(str(v) for v in row)
            if len(row_text) > 155:
                row_text = f"{row_text[:152]}..."
            pdf.drawString(40, y, row_text)
            y -= 12

        pdf.save()
        data = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        response.write(data)
        return response

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title=project.name,
                url=None,
            ),
            BreadcrumbItem(
                title="Compliance Report",
                url=None,
            ),
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        project = self.get_project()

        period_key = (self.request.GET.get("period") or "1m").lower()
        period_start, period_end, period_label = self._get_reporting_window(period_key)

        context.update(
            {
                "project": project,
                "period_key": period_key,
                "period_label": period_label,
                "period_start": period_start,
                "period_end": period_end,
                "tab": "compliance_report",
            }
        )

        # Get Report Summary for qualitative data
        summary = ProjectReportSummary.objects.filter(
            project=project, period_start__lte=period_end, period_end__gte=period_start
        ).first()

        # -----------------------------
        # Project Information (Section 1)
        # -----------------------------
        consultants = project.lead_consultants.all()
        context["consultants"] = ", ".join(
            [(c.get_full_name() or c.email or str(c.pk)) for c in consultants]
        )
        context["client"] = project.client.name if project.client else "-"
        context["contractor"] = project.contractor.name if project.contractor else "-"
        context["contract_reference"] = project.contract_number or "-"

        # Determine dynamic summaries from ProjectReportSummary
        status_summary = (
            summary.project_status_summary
            if summary and summary.project_status_summary
            else f"Compliance review for {period_label}. All registers active."
        )
        recommendations_text = (
            summary.recommendations
            if summary and summary.recommendations
            else "Ensure all compliance documents are updated."
        )

        context.update(
            {
                "project_status_summary": status_summary,
                "recommendations_text": recommendations_text,
            }
        )

        # -----------------------------
        # Compliance Registers
        # -----------------------------

        # Contractual Compliance
        contractual_items = ContractualCompliance.objects.filter(
            project=project, deleted=False
        )
        contractual_in_period = contractual_items.filter(
            due_date__range=(period_start, period_end)
        )
        contractual_completed = contractual_in_period.filter(
            status=ContractualCompliance.Status.COMPLETED
        )
        contractual_overdue = contractual_in_period.filter(
            status=ContractualCompliance.Status.OVERDUE
        )

        # Administrative Compliance
        admin_items = AdministrativeCompliance.objects.filter(
            project=project, deleted=False
        )
        admin_in_period = admin_items.filter(
            Q(submission_due_date__range=(period_start, period_end))
            | Q(approval_due_date__range=(period_start, period_end))
        )
        admin_approved = admin_in_period.filter(
            status=AdministrativeCompliance.Status.APPROVED
        )
        admin_overdue = admin_in_period.filter(
            status=AdministrativeCompliance.Status.OVERDUE
        )

        # Final Account Compliance
        final_items = FinalAccountCompliance.objects.filter(
            project=project, deleted=False
        )
        final_in_period = final_items.filter(
            Q(submission_date__range=(period_start, period_end))
            | Q(approval_date__range=(period_start, period_end))
        )
        final_approved = final_in_period.filter(
            status=FinalAccountCompliance.Status.APPROVED
        )

        # Non-Conformances (NCRs)
        ncrs = NonConformance.objects.filter(project=project).order_by("-date")
        ncrs_in_period = ncrs.filter(date__range=(period_start, period_end))
        ncrs_open = ncrs_in_period.filter(status=NCRStatus.OPEN)
        ncrs_closed = ncrs_in_period.filter(status=NCRStatus.CLOSED)

        # Incidents
        incidents = Incident.objects.filter(project=project)
        incidents_in_period = incidents.filter(date__range=(period_start, period_end))
        incidents_open = incidents_in_period.filter(status=IncidentStatus.OPEN)
        incidents_closed = incidents_in_period.filter(status=IncidentStatus.CLOSED)

        # Early Warnings
        early_warnings = EarlyWarning.objects.filter(project=project)
        early_warnings_in_period = early_warnings.filter(
            date__range=(period_start, period_end)
        )
        early_warnings_open = early_warnings_in_period.filter(
            status=EarlyWarningStatus.OPEN
        )
        early_warnings_closed = early_warnings_in_period.filter(
            status=EarlyWarningStatus.CLOSED
        )

        # Quality Reports
        quality_reports = BiWeeklyQualityReport.objects.filter(project=project)
        quality_reports_in_period = quality_reports.filter(
            period_end__range=(period_start, period_end)
        )

        # Safety Reports
        safety_reports = BiWeeklySafetyReport.objects.filter(project=project)
        safety_reports_in_period = safety_reports.filter(
            period_end__range=(period_start, period_end)
        )

        # RFIs
        rfis = RFI.objects.filter(project=project)
        rfis_in_period = rfis.filter(date_issued__range=(period_start, period_end))
        rfis_responded = rfis_in_period.filter(status=RFIStatus.CLOSED)

        # Site Instructions
        site_instructions = SiteInstruction.objects.filter(project=project)
        site_instructions_in_period = site_instructions.filter(
            date_notified__range=(period_start, period_end)
        )
        site_instructions_confirmed = site_instructions_in_period.filter(
            status=SiteInstructionStatus.CLOSED
        )

        # Build register overview
        context["register_overview"] = [
            {
                "register_type": "Contractual Compliance",
                "tab_url": reverse(
                    "project:contractual-compliance-list", args=[project.pk]
                ),
                "total_to_date": contractual_items.count(),
                "current_entries": contractual_in_period.count(),
                "open_items": contractual_in_period.exclude(
                    status__in=[
                        ContractualCompliance.Status.COMPLETED,
                        ContractualCompliance.Status.NOT_APPLICABLE,
                    ]
                ).count(),
                "closed_percentage": round(
                    (
                        contractual_completed.count()
                        / contractual_in_period.count()
                        * 100
                    ),
                    1,
                )
                if contractual_in_period.count()
                else 0,
                "open_percentage": round(
                    (contractual_overdue.count() / contractual_in_period.count() * 100),
                    1,
                )
                if contractual_in_period.count()
                else 0,
                "impact_value": None,
            },
            {
                "register_type": "Administrative Compliance",
                "tab_url": reverse(
                    "project:administrative-compliance-list", args=[project.pk]
                ),
                "total_to_date": admin_items.count(),
                "current_entries": admin_in_period.count(),
                "open_items": admin_in_period.exclude(
                    status=AdministrativeCompliance.Status.APPROVED
                ).count(),
                "closed_percentage": round(
                    (admin_approved.count() / admin_in_period.count() * 100), 1
                )
                if admin_in_period.count()
                else 0,
                "open_percentage": round(
                    (admin_overdue.count() / admin_in_period.count() * 100), 1
                )
                if admin_in_period.count()
                else 0,
                "impact_value": None,
            },
            {
                "register_type": "Final Account Compliance",
                "tab_url": reverse(
                    "project:final-account-compliance-list", args=[project.pk]
                ),
                "total_to_date": final_items.count(),
                "current_entries": final_in_period.count(),
                "open_items": final_in_period.exclude(
                    status=FinalAccountCompliance.Status.APPROVED
                ).count(),
                "closed_percentage": round(
                    (final_approved.count() / final_in_period.count() * 100), 1
                )
                if final_in_period.count()
                else 0,
                "open_percentage": 0,  # Final account items don't have overdue status
                "impact_value": None,
            },
            {
                "register_type": "Non-Conformance Reports",
                "tab_url": reverse("site_management:ncr-list", args=[project.pk]),
                "total_to_date": ncrs.count(),
                "current_entries": ncrs_in_period.count(),
                "open_items": ncrs_open.count(),
                "closed_percentage": round(
                    (ncrs_closed.count() / ncrs_in_period.count() * 100), 1
                )
                if ncrs_in_period.count()
                else 0,
                "open_percentage": round(
                    (ncrs_open.count() / ncrs_in_period.count() * 100), 1
                )
                if ncrs_in_period.count()
                else 0,
                "impact_value": None,
            },
            {
                "register_type": "Incidents",
                "tab_url": reverse("site_management:incident-list", args=[project.pk]),
                "total_to_date": incidents.count(),
                "current_entries": incidents_in_period.count(),
                "open_items": incidents_open.count(),
                "closed_percentage": round(
                    (incidents_closed.count() / incidents_in_period.count() * 100), 1
                )
                if incidents_in_period.count()
                else 0,
                "open_percentage": round(
                    (incidents_open.count() / incidents_in_period.count() * 100), 1
                )
                if incidents_in_period.count()
                else 0,
                "impact_value": None,
            },
            {
                "register_type": "Early Warnings",
                "tab_url": reverse(
                    "site_management:early-warning-list", args=[project.pk]
                ),
                "total_to_date": early_warnings.count(),
                "current_entries": early_warnings_in_period.count(),
                "open_items": early_warnings_open.count(),
                "closed_percentage": round(
                    (
                        early_warnings_closed.count()
                        / early_warnings_in_period.count()
                        * 100
                    ),
                    1,
                )
                if early_warnings_in_period.count()
                else 0,
                "open_percentage": round(
                    (
                        early_warnings_open.count()
                        / early_warnings_in_period.count()
                        * 100
                    ),
                    1,
                )
                if early_warnings_in_period.count()
                else 0,
                "impact_value": None,
            },
            {
                "register_type": "Quality Reports",
                "tab_url": reverse(
                    "site_management:biweekly-quality-list", args=[project.pk]
                ),
                "total_to_date": quality_reports.count(),
                "current_entries": quality_reports_in_period.count(),
                "open_items": quality_reports_in_period.count(),  # All reports are "open" until period ends
                "closed_percentage": 0,
                "open_percentage": 100,
                "impact_value": None,
            },
            {
                "register_type": "Safety Reports",
                "tab_url": reverse(
                    "site_management:biweekly-safety-list", args=[project.pk]
                ),
                "total_to_date": safety_reports.count(),
                "current_entries": safety_reports_in_period.count(),
                "open_items": safety_reports_in_period.count(),  # All reports are "open" until period ends
                "closed_percentage": 0,
                "open_percentage": 100,
                "impact_value": None,
            },
            {
                "register_type": "RFIs",
                "tab_url": reverse("site_management:rfi-list", args=[project.pk]),
                "total_to_date": rfis.count(),
                "current_entries": rfis_in_period.count(),
                "open_items": rfis_in_period.exclude(status=RFIStatus.CLOSED).count(),
                "closed_percentage": round(
                    (rfis_responded.count() / rfis_in_period.count() * 100), 1
                )
                if rfis_in_period.count()
                else 0,
                "open_percentage": round(
                    (
                        rfis_in_period.exclude(status=RFIStatus.CLOSED).count()
                        / rfis_in_period.count()
                        * 100
                    ),
                    1,
                )
                if rfis_in_period.count()
                else 0,
                "impact_value": None,
            },
            {
                "register_type": "Site Instructions",
                "tab_url": reverse(
                    "site_management:site-instruction-list", args=[project.pk]
                ),
                "total_to_date": site_instructions.count(),
                "current_entries": site_instructions_in_period.count(),
                "open_items": site_instructions_in_period.exclude(
                    status=SiteInstructionStatus.CLOSED
                ).count(),
                "closed_percentage": round(
                    (
                        site_instructions_confirmed.count()
                        / site_instructions_in_period.count()
                        * 100
                    ),
                    1,
                )
                if site_instructions_in_period.count()
                else 0,
                "open_percentage": round(
                    (
                        site_instructions_in_period.exclude(
                            status=SiteInstructionStatus.CLOSED
                        ).count()
                        / site_instructions_in_period.count()
                        * 100
                    ),
                    1,
                )
                if site_instructions_in_period.count()
                else 0,
                "impact_value": None,
            },
        ]

        # Extract small sets for template display
        context.update(
            {
                "contractual_compliance": contractual_in_period.order_by("-due_date")[
                    :10
                ],
                "administrative_compliance": admin_in_period.order_by(
                    "-submission_due_date"
                )[:10],
                "final_account_compliance": final_in_period.order_by(
                    "-submission_date"
                )[:10],
                "ncrs": ncrs_in_period.order_by("-date")[:10],
                "incidents": incidents_in_period.order_by("-date")[:10],
                "early_warnings": early_warnings_in_period.order_by("-date")[:10],
                "quality_reports": quality_reports_in_period.order_by("-period_end")[
                    :5
                ],
                "safety_reports": safety_reports_in_period.order_by("-period_end")[:5],
                "rfis": rfis_in_period.order_by("-date_issued")[:10],
                "site_instructions": site_instructions_in_period.order_by(
                    "-date_notified"
                )[:10],
            }
        )

        return context


class ActionTrackerReportView(ComplianceReportView):
    """Report that tracks all actions across meetings and registers in a unified list."""

    template_name = "project/action_tracker_report.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(title="Projects", url=reverse("project:project-list")),
            BreadcrumbItem(
                title=project.name,
                url=reverse(
                    "project:project-management",
                    kwargs={"pk": project.pk},
                ),
            ),
            BreadcrumbItem(
                title="Meetings",
                url=reverse("site_management:meeting-list", args=[project.pk]),
            ),
            BreadcrumbItem(title="Action Tracker", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        today = timezone.now().date()

        actions = []

        # 1. Meeting Actions
        meeting_actions = MeetingAction.objects.filter(
            meeting__project=project, deleted=False
        ).exclude(status=MeetingActionStatus.COMPLETE)
        for ma in meeting_actions:
            actions.append(
                {
                    "source": "Meeting",
                    "description": ma.description,
                    "responsible": ma.assigned_to,
                    "due_date": ma.due_date,
                    "status": ma.get_status_display(),
                    "link": reverse(
                        "site_management:meeting-detail",
                        args=[project.pk, ma.meeting.pk],
                    ),
                }
            )

        # 2. Open Non-Conformances
        open_ncrs = NonConformance.objects.filter(
            project=project, status=NCRStatus.OPEN, deleted=False
        ).select_related("source_decision__meeting")
        for ncr in open_ncrs:
            source = "NCR"
            if ncr.source_decision:
                source = f"NCR (Meeting {ncr.source_decision.meeting.date.strftime('%d/%m')})"
            actions.append(
                {
                    "source": source,
                    "description": f"{ncr.reference_number}: {ncr.description}",
                    "responsible": ncr.responsible_person,
                    "due_date": ncr.date,
                    "status": "Open",
                    "link": reverse("site_management:ncr-list", args=[project.pk]),
                }
            )

        # 3. Open Incidents
        open_incidents = Incident.objects.filter(
            project=project, status=IncidentStatus.OPEN, deleted=False
        )
        for inc in open_incidents:
            actions.append(
                {
                    "source": "Incident",
                    "description": f"{inc.reference_number}: {inc.description}",
                    "responsible": inc.reported_by,
                    "due_date": inc.date,
                    "status": "Open",
                    "link": reverse("site_management:incident-list", args=[project.pk]),
                }
            )

        # 4. Open RFIs
        open_rfis = RFI.objects.filter(
            project=project, status=RFIStatus.OPEN, deleted=False
        ).select_related("source_decision__meeting")
        for rfi in open_rfis:
            source = "RFI"
            if rfi.source_decision:
                source = f"RFI (Meeting {rfi.source_decision.meeting.date.strftime('%d/%m')})"
            actions.append(
                {
                    "source": source,
                    "description": f"{rfi.reference_number}: {rfi.subject}",
                    "responsible": "Consultant/Client",
                    "due_date": rfi.due_date,
                    "status": "Open",
                    "link": reverse(
                        "site_management:rfi-detail", args=[project.pk, rfi.pk]
                    ),
                }
            )

        # 5. Open Site Instructions
        open_sis = SiteInstruction.objects.filter(
            project=project, status=SiteInstructionStatus.OPEN, deleted=False
        ).select_related("source_decision__meeting")
        for si in open_sis:
            source = "Site Instruction"
            if si.source_decision:
                source = (
                    f"SI (Meeting {si.source_decision.meeting.date.strftime('%d/%m')})"
                )
            actions.append(
                {
                    "source": source,
                    "description": f"{si.reference_number}: {si.subject}",
                    "responsible": "Contractor",
                    "due_date": si.date_notified,
                    "status": "Open",
                    "link": reverse(
                        "site_management:site-instruction-detail",
                        args=[project.pk, si.pk],
                    ),
                }
            )

        # 6. Open Early Warnings
        open_ewns = EarlyWarning.objects.filter(
            project=project, status=EarlyWarningStatus.OPEN, deleted=False
        ).select_related("source_decision__meeting")
        for ew in open_ewns:
            source = "Early Warning"
            if ew.source_decision:
                source = (
                    f"EW (Meeting {ew.source_decision.meeting.date.strftime('%d/%m')})"
                )
            actions.append(
                {
                    "source": source,
                    "description": f"{ew.reference_number}: {ew.subject}",
                    "responsible": "Project Manager",
                    "due_date": ew.date,
                    "status": "Open",
                    "link": reverse(
                        "site_management:early-warning-list", args=[project.pk]
                    ),
                }
            )

        # 7. Open Variations
        open_variations = ContractVariation.objects.filter(
            project=project, deleted=False
        ).exclude(
            status__in=[
                ContractVariation.Status.APPROVED,
                ContractVariation.Status.REJECTED,
            ]
        )
        for var in open_variations:
            actions.append(
                {
                    "source": "Variation",
                    "description": f"VO-{var.variation_number}: {var.title}",
                    "responsible": "Quantity Surveyor",
                    "due_date": var.date_identified,
                    "status": var.get_status_display(),
                    "link": "#",
                }
            )

        # 8. Open Correspondence
        open_correspondence = ContractualCorrespondence.objects.filter(
            project=project, requires_response=True, response_sent=False, deleted=False
        )
        for corr in open_correspondence:
            actions.append(
                {
                    "source": "Correspondence",
                    "description": f"{corr.reference_number}: {corr.subject}",
                    "responsible": "Project Team",
                    "due_date": corr.response_due_date,
                    "status": "Pending Response",
                    "link": "#",
                }
            )

        # Sort actions by due date (overdue first)
        actions.sort(key=lambda x: x["due_date"] if x["due_date"] else date.max)

        context.update(
            {
                "unified_actions": actions,
                "today": today,
                "tab": "action_tracker",
            }
        )
        return context


class DecisionLogReportView(ComplianceReportView):
    """Report that tracks all key decisions across all project meetings."""

    template_name = "project/decision_log_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()

        decisions = MeetingDecision.objects.filter(
            meeting__project=project, deleted=False
        ).order_by("-meeting__date", "-created_at")

        context.update(
            {
                "decisions": decisions,
                "today": timezone.now().date(),
                "tab": "decision_log",
            }
        )
        return context
