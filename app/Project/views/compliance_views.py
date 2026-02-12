"""Views for Compliance Management.

This module contains views for managing contractual, administrative,
and final account compliance items.
"""

from django.contrib import messages
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms import (
    AdministrativeComplianceForm,
    ContractualComplianceForm,
    FinalAccountComplianceForm,
)
from app.Project.models import (
    AdministrativeCompliance,
    ContractualCompliance,
    FinalAccountCompliance,
    Role,
)


class ComplianceMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for compliance views."""

    roles = [Role.USER]
    project_slug = "project_pk"

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


# =============================================================================
# Compliance Dashboard View
# =============================================================================


class ComplianceDashboardView(ComplianceMixin, TemplateView):
    """Dashboard view showing all compliance tabs."""

    template_name = "compliance/compliance_dashboard.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(title="Compliance Management", url=None),
        ]

    def get_context_data(self, **kwargs):
        """Add compliance items to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()

        # Get counts and recent items for each compliance type
        context["contractual_items"] = ContractualCompliance.objects.filter(
            project=project
        )
        context["contractual_count"] = context["contractual_items"].count()
        context["contractual_pending"] = (
            context["contractual_items"]
            .filter(
                status__in=[
                    ContractualCompliance.Status.PENDING,
                    ContractualCompliance.Status.IN_PROGRESS,
                ]
            )
            .count()
        )

        context["administrative_items"] = AdministrativeCompliance.objects.filter(
            project=project
        )
        context["administrative_count"] = context["administrative_items"].count()
        context["administrative_pending"] = (
            context["administrative_items"]
            .filter(
                status__in=[
                    AdministrativeCompliance.Status.DRAFT,
                    AdministrativeCompliance.Status.SUBMITTED,
                    AdministrativeCompliance.Status.UNDER_REVIEW,
                ]
            )
            .count()
        )

        context["final_account_items"] = FinalAccountCompliance.objects.filter(
            project=project
        )
        context["final_account_count"] = context["final_account_items"].count()
        context["final_account_pending"] = (
            context["final_account_items"]
            .filter(
                status__in=[
                    FinalAccountCompliance.Status.REQUIRED,
                    FinalAccountCompliance.Status.REQUESTED,
                    FinalAccountCompliance.Status.SUBMITTED,
                    FinalAccountCompliance.Status.UNDER_REVIEW,
                ]
            )
            .count()
        )

        # Active tab from URL
        context["active_tab"] = self.request.GET.get("tab", "contractual")

        return context


# =============================================================================
# Contractual Compliance Views
# =============================================================================


class ContractualComplianceListView(ComplianceMixin, ListView):
    """List all contractual compliance items for a project."""

    model = ContractualCompliance
    template_name = "compliance/contractual/list.html"
    context_object_name = "items"

    def get_queryset(self) -> QuerySet[ContractualCompliance]:
        return ContractualCompliance.objects.filter(
            project=self.get_project()
        ).order_by("due_date", "-created_at")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Compliance Management",
                url=reverse(
                    "project:compliance-dashboard",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Contractual Compliance", url=None),
        ]


class ContractualComplianceCreateView(ComplianceMixin, CreateView):
    """Create a new contractual compliance item."""

    model = ContractualCompliance
    form_class = ContractualComplianceForm
    template_name = "compliance/contractual/form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Compliance Management",
                url=reverse(
                    "project:compliance-dashboard",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(
                title="Contractual Compliance",
                url=reverse(
                    "project:contractual-compliance-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Add New", url=None),
        ]

    def form_valid(self, form):
        form.instance.project = self.get_project()
        form.instance.created_by = self.request.user
        messages.success(self.request, "Contractual compliance item created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "project:contractual-compliance-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class ContractualComplianceUpdateView(ComplianceMixin, UpdateView):
    """Update a contractual compliance item."""

    model = ContractualCompliance
    form_class = ContractualComplianceForm
    template_name = "compliance/contractual/form.html"

    def get_object(self, queryset=None) -> ContractualCompliance:
        if not queryset:
            self.get_queryset()
        return get_object_or_404(
            ContractualCompliance,
            pk=self.kwargs["pk"],
            project__pk=self.kwargs["project_pk"],
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Compliance Management",
                url=reverse(
                    "project:compliance-dashboard",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(
                title="Contractual Compliance",
                url=reverse(
                    "project:contractual-compliance-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Edit", url=None),
        ]

    def form_valid(self, form):
        messages.success(self.request, "Contractual compliance item updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "project:contractual-compliance-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class ContractualComplianceDeleteView(ComplianceMixin, DeleteView):
    """Delete a contractual compliance item."""

    model = ContractualCompliance
    template_name = "compliance/contractual/confirm_delete.html"

    def get_object(self, queryset=None) -> ContractualCompliance:
        self.get_queryset() if not queryset else None
        return get_object_or_404(
            ContractualCompliance,
            pk=self.kwargs["pk"],
            project__pk=self.kwargs["project_pk"],
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Contractual Compliance",
                url=reverse(
                    "project:contractual-compliance-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Delete", url=None),
        ]

    def form_valid(self, form):
        obj = self.get_object()
        obj.soft_delete()
        messages.success(self.request, "Contractual compliance item deleted.")
        return redirect(str(self.get_success_url()))

    def get_success_url(self):
        return reverse_lazy(
            "project:contractual-compliance-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


# =============================================================================
# Administrative Compliance Views
# =============================================================================


class AdministrativeComplianceListView(ComplianceMixin, ListView):
    """List all administrative compliance items for a project."""

    model = AdministrativeCompliance
    template_name = "compliance/administrative/list.html"
    context_object_name = "items"

    def get_queryset(self) -> QuerySet[AdministrativeCompliance]:
        return AdministrativeCompliance.objects.filter(
            project=self.get_project()
        ).order_by("submission_due_date", "-created_at")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Compliance Management",
                url=reverse(
                    "project:compliance-dashboard",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Administrative Compliance", url=None),
        ]


class AdministrativeComplianceCreateView(ComplianceMixin, CreateView):
    """Create a new administrative compliance item."""

    model = AdministrativeCompliance
    form_class = AdministrativeComplianceForm
    template_name = "compliance/administrative/form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Compliance Management",
                url=reverse(
                    "project:compliance-dashboard",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(
                title="Administrative Compliance",
                url=reverse(
                    "project:administrative-compliance-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Add New", url=None),
        ]

    def form_valid(self, form):
        form.instance.project = self.get_project()
        form.instance.created_by = self.request.user
        messages.success(self.request, "Administrative compliance item created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "project:administrative-compliance-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class AdministrativeComplianceUpdateView(ComplianceMixin, UpdateView):
    """Update an administrative compliance item."""

    model = AdministrativeCompliance
    form_class = AdministrativeComplianceForm
    template_name = "compliance/administrative/form.html"

    def get_object(self, queryset=None) -> AdministrativeCompliance:
        if not queryset:
            self.get_queryset()
        return get_object_or_404(
            AdministrativeCompliance,
            pk=self.kwargs["pk"],
            project__pk=self.kwargs["project_pk"],
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Compliance Management",
                url=reverse(
                    "project:compliance-dashboard",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(
                title="Administrative Compliance",
                url=reverse(
                    "project:administrative-compliance-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Edit", url=None),
        ]

    def form_valid(self, form):
        messages.success(self.request, "Administrative compliance item updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "project:administrative-compliance-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class AdministrativeComplianceDeleteView(ComplianceMixin, DeleteView):
    """Delete an administrative compliance item."""

    model = AdministrativeCompliance
    template_name = "compliance/administrative/confirm_delete.html"

    def get_object(self, queryset=None) -> AdministrativeCompliance:
        if not queryset:
            self.get_queryset()
        return get_object_or_404(
            AdministrativeCompliance,
            pk=self.kwargs["pk"],
            project__pk=self.kwargs["project_pk"],
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Administrative Compliance",
                url=reverse(
                    "project:administrative-compliance-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Delete", url=None),
        ]

    def form_valid(self, form):
        obj = self.get_object()
        obj.soft_delete()
        messages.success(self.request, "Administrative compliance item deleted.")
        return redirect(str(self.get_success_url()))

    def get_success_url(self):
        return reverse_lazy(
            "project:administrative-compliance-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


# =============================================================================
# Final Account Compliance Views
# =============================================================================


class FinalAccountComplianceListView(ComplianceMixin, ListView):
    """List all final account compliance items for a project."""

    model = FinalAccountCompliance
    template_name = "compliance/final_account/list.html"
    context_object_name = "items"

    def get_queryset(self) -> QuerySet[FinalAccountCompliance]:
        return FinalAccountCompliance.objects.filter(
            project=self.get_project()
        ).order_by("document_type", "-created_at")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Compliance Management",
                url=reverse(
                    "project:compliance-dashboard",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Final Account Compliance", url=None),
        ]


class FinalAccountComplianceCreateView(ComplianceMixin, CreateView):
    """Create a new final account compliance item."""

    model = FinalAccountCompliance
    form_class = FinalAccountComplianceForm
    template_name = "compliance/final_account/form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Compliance Management",
                url=reverse(
                    "project:compliance-dashboard",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(
                title="Final Account Compliance",
                url=reverse(
                    "project:final-account-compliance-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Add New", url=None),
        ]

    def form_valid(self, form):
        form.instance.project = self.get_project()
        form.instance.created_by = self.request.user
        messages.success(self.request, "Final account compliance item created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "project:final-account-compliance-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class FinalAccountComplianceUpdateView(ComplianceMixin, UpdateView):
    """Update a final account compliance item."""

    model = FinalAccountCompliance
    form_class = FinalAccountComplianceForm
    template_name = "compliance/final_account/form.html"

    def get_object(self, queryset=None) -> FinalAccountCompliance:
        if not queryset:
            self.get_queryset()
        return get_object_or_404(
            FinalAccountCompliance,
            pk=self.kwargs["pk"],
            project__pk=self.kwargs["project_pk"],
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Compliance Management",
                url=reverse(
                    "project:compliance-dashboard",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(
                title="Final Account Compliance",
                url=reverse(
                    "project:final-account-compliance-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Edit", url=None),
        ]

    def form_valid(self, form):
        messages.success(self.request, "Final account compliance item updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "project:final-account-compliance-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class FinalAccountComplianceDeleteView(ComplianceMixin, DeleteView):
    """Delete a final account compliance item."""

    model = FinalAccountCompliance
    template_name = "compliance/final_account/confirm_delete.html"

    def get_object(self, queryset=None) -> FinalAccountCompliance:
        self.get_queryset() if not queryset else None
        return get_object_or_404(
            FinalAccountCompliance,
            pk=self.kwargs["pk"],
            project__pk=self.kwargs["project_pk"],
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Final Account Compliance",
                url=reverse(
                    "project:final-account-compliance-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Delete", url=None),
        ]

    def form_valid(self, form):
        obj = self.get_object()
        obj.soft_delete()
        messages.success(self.request, "Final account compliance item deleted.")
        return redirect(str(self.get_success_url()))

    def get_success_url(self):
        return reverse_lazy(
            "project:final-account-compliance-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )
