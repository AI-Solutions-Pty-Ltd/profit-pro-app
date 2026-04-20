"""Views for Company model."""

import json
import random
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, QuerySet, Sum
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.core.Utilities.dates import get_previous_n_months
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Estimator.models import BOQItem
from app.Project.models import (
    Company,
    ContractualCompliance,
    OverheadCostTracker,
    Portfolio,
    Project,
)

from .company_forms import CompanyFilterForm, CompanyForm


class CompanyMetricsMixin:
    """Mixin to calculate financial metrics for companies and projects."""

    def get_metrics_context(self, projects: QuerySet[Project]) -> dict:
        """Calculate financial metrics for a given set of projects."""
        current_date = datetime.now()
        total_baseline_revenue = 0
        total_baseline_cost = 0
        total_progress_revenue = 0
        total_progress_cost = 0
        total_forecast_revenue = 0
        total_forecast_cost = 0
        total_overheads = 0

        for project in projects:
            # Aggregating BOQ items for this project
            boq_items = BOQItem.objects.filter(project=project)
            for item in boq_items:
                # Baseline
                rev = float(item.contract_amount or 0)
                cost = float(item.baseline_new_price or 0) * float(
                    item.contract_quantity or 0
                )
                total_baseline_revenue += rev
                total_baseline_cost += cost

                # Progress
                p_rev = float(item.progress_amount or 0)
                p_cost = float(item.baseline_new_price or 0) * float(
                    item.progress_quantity or 0
                )
                total_progress_revenue += p_rev
                total_progress_cost += p_cost

                # Forecast
                f_rev = float(item.forecast_amount or 0)
                f_cost = float(item.baseline_new_price or 0) * float(
                    item.forecast_quantity or 0
                )
                total_forecast_revenue += f_rev
                total_forecast_cost += f_cost

            # Overheads
            project_overheads = (
                OverheadCostTracker.objects.filter(project=project).aggregate(
                    total=Sum(F("amount_of_days") * F("rate"))
                )["total"]
                or 0
            )
            total_overheads += float(project_overheads)

        baseline_profit = total_baseline_revenue - total_baseline_cost
        progress_profit = total_progress_revenue - total_progress_cost
        forecast_profit = total_forecast_revenue - total_forecast_cost

        # Compliance Stats
        total_compliance_items = ContractualCompliance.objects.filter(
            project__in=projects
        ).count()
        completed_compliance_items = ContractualCompliance.objects.filter(
            project__in=projects,
            status=ContractualCompliance.Status.COMPLETED,
        ).count()
        urgent_compliance_count = ContractualCompliance.objects.filter(
            project__in=projects,
            status=ContractualCompliance.Status.OVERDUE,
        ).count()

        compliance_percentage = (
            round((completed_compliance_items / total_compliance_items * 100), 1)
            if total_compliance_items > 0
            else 0
        )

        metrics = {
            "current_date": current_date,
            "revenue": total_baseline_revenue,
            "baseline_profit": baseline_profit,
            "baseline_profit_margin": (
                (baseline_profit / total_baseline_revenue * 100)
                if total_baseline_revenue > 0
                else 0
            ),
            "progress_profit": progress_profit,
            "progress_profit_margin": (
                (progress_profit / total_progress_revenue * 100)
                if total_progress_revenue > 0
                else 0
            ),
            "forecast_profit": forecast_profit,
            "forecast_profit_margin": (
                (forecast_profit / total_forecast_revenue * 100)
                if total_forecast_revenue > 0
                else 0
            ),
            "total_overheads": total_overheads,
            "overheads_percentage": (
                (total_overheads / total_baseline_revenue * 100)
                if total_baseline_revenue > 0
                else 0
            ),
            "compliance_percentage": compliance_percentage,
            "total_compliance_items": total_compliance_items,
            "urgent_compliance_count": urgent_compliance_count,
        }

        # Profit trend data for charts
        profit_data = self._get_profit_trend_data()
        metrics.update(
            {
                "profit_labels": json.dumps(profit_data["labels"]),
                "gross_profit_percentage_data": json.dumps(
                    profit_data["gross_profit_percentages"]
                ),
                "net_profit_data": json.dumps(profit_data["net_profit_values"]),
            }
        )
        return metrics

    def _get_profit_trend_data(self) -> dict:
        """Generate 6 months of profit trend data for charts."""
        labels = [month.strftime("%b %Y") for month in get_previous_n_months(6)]
        gross_profit_percentages = [round(random.uniform(10, 30), 1) for _ in range(6)]
        net_profit_values = [
            round(random.uniform(500000, 1500000), 0) for _ in range(6)
        ]
        return {
            "labels": labels,
            "gross_profit_percentages": gross_profit_percentages,
            "net_profit_values": net_profit_values,
        }


class CompanyListView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """List all companies for the current user."""

    model: Project
    template_name = "company/company_list.html"
    context_object_name = "companies"
    paginate_by = 25
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self) -> QuerySet:
        """Filter companies to show only those the user has access to."""
        user: Account = self.request.user  # type: ignore
        return user.get_projects

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Business Dashbaord",
                "url": reverse("project:company-dashboard"),
            },
            {"title": "Companies", "url": None},
        ]


class CompanyManagementView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """Display company details and management options."""

    model = Company
    template_name = "company/company_management.html"
    context_object_name = "company"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Business Dashbaord",
                "url": reverse("project:company-dashboard"),
            },
            {
                "title": "Companies",
                "url": str(reverse_lazy("project:company-list")),
            },
            {"title": self.object.name, "url": None},
        ]

    def get_queryset(self) -> QuerySet["Project"]:
        """Filter companies to show only those the user has access to."""
        return self.request.user.get_projects  # type: ignore

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tab"] = "dashboard"
        return context


class CompanyUpdateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, UpdateView
):
    """Update a company."""

    model = Company
    form_class = CompanyForm
    template_name = "company/company_update.html"
    success_url = reverse_lazy("project:company-list")
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self) -> QuerySet:
        """Filter companies to show only those the user has access to."""
        return self.request.user.get_contractors  # type: ignore

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Update {self.object.name}"
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Home",
                "url": "/",
            },
            {
                "title": "Companies",
                "url": str(reverse_lazy("project:company-list")),
            },
            {"title": f"Update {self.object.name}", "url": None},
        ]


class CompanyDashboardView(
    SubscriptionRequiredMixin, BreadcrumbMixin, CompanyMetricsMixin, ListView
):
    """Projects dashboard showing financial metrics for Portfolio."""

    model = Project
    template_name = "company/company_dashboard.html"
    context_object_name = "projects"
    required_tiers = [Subscription.BUSINESS_MANAGEMENT]

    def get_breadcrumbs(self: "CompanyDashboardView") -> list[BreadcrumbItem]:
        return [
            {"title": "Business Dashboard", "url": None},
        ]

    def get_queryset(self: "CompanyDashboardView") -> QuerySet[Project]:
        """Get filtered projects for dashboard view."""
        # Initialize filter form with user's projects
        user: Account = self.request.user  # type: ignore
        return user.get_projects

    def get(self, request, *args, **kwargs):
        """Handle GET request and check for project redirect."""
        # Initialize filter form with user's projects
        user: Account = self.request.user  # type: ignore

        # Initialize filter form with the base queryset
        filter_form = CompanyFilterForm(self.request.GET or {}, user=user)

        if filter_form.is_valid():
            company = filter_form.cleaned_data.get("company")
            if company:
                return redirect(
                    "project:company-management",
                    pk=company.pk,
                )

        # Continue with normal GET processing
        return super().get(request, *args, **kwargs)

    def get_context_data(self: "CompanyDashboardView", **kwargs):
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)
        user: Account = self.request.user  # type: ignore
        active_projects = self.get_queryset()

        if user.portfolio:
            portfolio = user.portfolio
        else:
            portfolio = Portfolio.objects.create()
            portfolio.users.add(user)
            user.get_projects.update(portfolio=portfolio)

        filter_form = CompanyFilterForm(
            self.request.GET or None, user=self.request.user
        )

        # Add the already-validated form to context
        context["filter_form"] = filter_form
        current_date = datetime.now()
        context["current_date"] = current_date

        # Highlights
        context["active_companies"] = (
            active_projects.values("contractor").distinct().count()
        )
        context["urgent_projects_count"] = len(
            portfolio.get_projects_requiring_urgent_intervention(current_date)
        )
        context["attention_projects_count"] = len(
            portfolio.get_projects_requiring_attention(current_date)
        )

        # Use mixin to get metrics
        metrics = self.get_metrics_context(active_projects)
        context.update(metrics)

        return context


class CompanyDetailDashboardView(
    SubscriptionRequiredMixin, BreadcrumbMixin, CompanyMetricsMixin, DetailView
):
    """Dedicated dashboard for a single company."""

    model = Company
    template_name = "company/company_detail_dashboard.html"
    context_object_name = "company"
    required_tiers = [Subscription.BUSINESS_MANAGEMENT]

    def get(self, request, *args, **kwargs):
        """Redirect to company management as detail dashboard is disabled."""
        self.object = self.get_object()
        return redirect("project:company-management", pk=self.object.pk)

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Business Dashboard",
                "url": reverse("project:company-dashboard"),
            },
            {
                "title": "Companies",
                "url": reverse("project:company-list"),
            },
            {"title": self.object.name, "url": None},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.object

        # Get projects related to this company (as contractor)
        projects = Project.objects.filter(contractor=company)

        # Use mixin to get metrics
        metrics = self.get_metrics_context(projects)
        context.update(metrics)

        context["active_projects_count"] = projects.count()
        context["tab"] = "dashboard"

        return context


class BusinessSetupView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """View for business setup configuration."""

    model = Company
    template_name = "company/business_setup.html"
    context_object_name = "company"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Business Dashboard",
                "url": reverse("project:company-dashboard"),
            },
            {
                "title": "Companies",
                "url": reverse("project:company-list"),
            },
            {
                "title": self.object.name,
                "url": reverse(
                    "project:company-management", kwargs={"pk": self.object.pk}
                ),
            },
            {"title": "Business Setup", "url": None},
        ]


class CompanyReportView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    model = Project
    template_name = "company/company_report.html"
    context_object_name = "company"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    report_titles = {
        "income_statement": "Income Statement",
        "production_report": "Production Report",
        "progress_report": "Progress Report",
        "cashflow_statement": "Cashflow Statement",
        "debtors_creditors": "Debtors & Creditors",
        "profitability_risk": "Profitability Risk Report",
        "contractors_report": "Contractors Report",
    }

    def get_queryset(self) -> QuerySet[Project]:
        return self.request.user.get_projects  # type: ignore

    def dispatch(self, request, *args, **kwargs):
        report = kwargs.get("report")
        if report not in self.report_titles:
            raise Http404("Unknown report")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.kwargs["report"]
        context["tab"] = report
        context["report"] = report
        context["report_title"] = self.report_titles[report]
        context["current_date"] = datetime.now()

        context["revenue"] = 100_000_000
        context["gross_profit_margin"] = 20.0
        context["gross_profit"] = 20_000_000
        context["variable_costs"] = 12_000_000
        context["net_profit"] = 8_000_000
        context["net_profit_margin"] = 8.0
        context["forecast_profit"] = 6_500_000
        return context
