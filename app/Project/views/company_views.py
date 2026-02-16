"""Views for Company model."""

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.Project.forms import CompanyForm
from app.Project.models import Company


class CompanyListView(LoginRequiredMixin, BreadcrumbMixin, ListView):
    """List all companies for the current user."""

    model: Any = None  # Will be set dynamically
    template_name = "company/company_list.html"
    context_object_name = "companies"
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        """Filter companies to show only those the user has access to."""
        return self.request.user.get_companies  # type: ignore

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Home",
                "url": "/",
            },
            {"title": "Companies", "url": None},
        ]


class CompanyDetailView(LoginRequiredMixin, BreadcrumbMixin, DetailView):
    """Display company details and management options."""

    model = Company
    template_name = "company/company_detail.html"
    context_object_name = "company"

    def get_queryset(self) -> QuerySet:
        """Filter companies to show only those the user has access to."""
        return self.request.user.get_companies  # type: ignore

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{self.object.name} - Company Details"
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
            {"title": self.object.name, "url": None},
        ]


class CompanyUpdateView(LoginRequiredMixin, BreadcrumbMixin, UpdateView):
    """Update a company."""

    model = Company
    form_class = CompanyForm
    template_name = "company/company_update.html"
    success_url = reverse_lazy("project:company-list")

    def get_queryset(self) -> QuerySet:
        """Filter companies to show only those the user has access to."""
        user = self.request.user
        if isinstance(user, Account) and user.is_superuser:
            return Company.objects.filter(type=Company.Type.CLIENT)
        if hasattr(user, "get_companies"):
            return user.get_companies  # type: ignore
        return Company.objects.none()

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
