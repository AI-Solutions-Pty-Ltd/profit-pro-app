"""Views for Company model."""

import json
import random
from datetime import datetime
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.core.Utilities.dates import get_previous_n_months
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Company

from .company_forms import CompanyFilterForm, CompanyForm


class CompanyListView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """List all companies for the current user."""

    model: Any = None  # Will be set dynamically
    template_name = "company/company_list.html"
    context_object_name = "companies"
    paginate_by = 25
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self) -> QuerySet:
        """Filter companies to show only those the user has access to."""
        user: Account = self.request.user  # type: ignore
        return user.get_contractors

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

    def get_queryset(self) -> QuerySet:
        """Filter companies to show only those the user has access to."""
        return self.request.user.get_contractors  # type: ignore


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


class CompanyDashboardView(SubscriptionRequiredMixin, BreadcrumbMixin, ListView):
    """Projects dashboard showing financial metrics for Portfolio."""

    model = Company
    template_name = "company/company_dashboard.html"
    context_object_name = "projects"
    required_tiers = [Subscription.BUSINESS_MANAGEMENT]

    def get_breadcrumbs(self: "CompanyDashboardView") -> list[BreadcrumbItem]:
        return [
            {"title": "Business Dashboard", "url": None},
        ]

    def get_queryset(self: "CompanyDashboardView") -> QuerySet[Company]:
        """Get filtered projects for dashboard view."""
        # Initialize filter form with user's projects
        user: Account = self.request.user  # type: ignore
        return user.get_contractors

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
                    "project:company-detail",
                    pk=company.pk,
                )

        # Continue with normal GET processing
        return super().get(request, *args, **kwargs)

    def get_context_data(self: "CompanyDashboardView", **kwargs):
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)

        filter_form = CompanyFilterForm(
            self.request.GET or None, user=self.request.user
        )

        # Add the already-validated form to context
        context["filter_form"] = filter_form
        context["current_date"] = datetime.now()

        # highlights
        context["active_companies"] = self.get_queryset().count()

        # Income Statement Summary (dummy data for now)
        context["revenue"] = 100_000_000
        context["gross_profit_margin"] = 20.0
        context["gross_profit"] = 20_000_000
        context["variable_costs"] = 12_000_000
        context["net_profit"] = 8_000_000
        context["net_profit_margin"] = 8.0
        context["forecast_profit"] = 6_500_000

        # Profit trend data for charts
        profit_data = self._get_profit_trend_data()
        context["profit_labels"] = json.dumps(profit_data["labels"])
        context["gross_profit_percentage_data"] = json.dumps(
            profit_data["gross_profit_percentages"]
        )
        context["net_profit_data"] = json.dumps(profit_data["net_profit_values"])

        return context

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
                "url": reverse("project:company-detail", kwargs={"pk": self.object.pk}),
            },
            {"title": "Business Setup", "url": None},
        ]
