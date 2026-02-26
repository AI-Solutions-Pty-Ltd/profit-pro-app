"""Views for managing contract variations and correspondence."""

from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.BillOfQuantities.models import (
    ContractVariation,
)
from app.core.Utilities.forms import styled_attachment_input, styled_date_input
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Role


class ContractVariationMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for contract variation views."""

    project_slug = "project_pk"
    roles = [Role.CONTRACT_VARIATIONS, Role.ADMIN, Role.USER]


class ContractVariationListView(ContractVariationMixin, ListView):
    """List all contract variations for a project."""

    model = ContractVariation
    template_name = "contract/variation_list.html"
    context_object_name = "variations"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": f"{self.get_project().name} Management",
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.kwargs["project_pk"]},
                ),
            },
            {"title": "Contract Variations", "url": None},
        ]

    def get_queryset(self):
        """Filter variations by project."""
        return ContractVariation.objects.filter(
            project=self.get_project(),
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        """Add project and summary stats to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        # Summary statistics
        variations = self.get_queryset()
        approved_variations = variations.filter(
            status=ContractVariation.Status.APPROVED
        )

        context["total_count"] = variations.count()
        context["approved_count"] = approved_variations.count()
        context["pending_count"] = variations.filter(
            status__in=[
                ContractVariation.Status.DRAFT,
                ContractVariation.Status.SUBMITTED,
                ContractVariation.Status.UNDER_REVIEW,
            ]
        ).count()

        # Total approved amounts
        context["total_approved_amount"] = sum_queryset(
            approved_variations, "variation_amount"
        )

        # Total approved time extensions
        context["total_approved_days"] = sum_queryset(
            approved_variations, "time_extension_days"
        )

        return context


class ContractVariationCreateView(ContractVariationMixin, CreateView):
    """Create a new contract variation."""

    model = ContractVariation
    template_name = "contract/variation_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": f"{self.get_project().name} Management",
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.kwargs["project_pk"]},
                ),
            },
            {
                "title": "Contract Variations",
                "url": reverse(
                    "bill_of_quantities:variation-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            },
            {"title": "Create Variation", "url": None},
        ]

    class CreateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date_identified"].widget = styled_date_input
            self.fields["attachment"].widget = styled_attachment_input
            # Status choices limited for create - starts as Draft
            self.fields["status"].initial = ContractVariation.Status.DRAFT

        class Meta:
            model = ContractVariation
            fields = [
                "title",
                "description",
                "category",
                "variation_type",
                "status",
                "variation_amount",
                "time_extension_days",
                "date_identified",
                "attachment",
            ]

    form_class = CreateForm

    def form_valid(self, form):
        """Set project and submitted_by before saving."""
        form.instance.project = self.get_project()
        form.instance.submitted_by = self.request.user
        messages.success(
            self.request,
            f"Contract Variation '{form.instance.variation_number}' created successfully!",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to variation list."""
        return reverse(
            "bill_of_quantities:variation-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = True
        return context


class ContractVariationUpdateView(ContractVariationMixin, UpdateView):
    """Update an existing contract variation."""

    model = ContractVariation
    template_name = "contract/variation_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": f"{self.get_project().name} Management",
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.kwargs["project_pk"]},
                ),
            },
            {
                "title": "Contract Variations",
                "url": reverse(
                    "bill_of_quantities:variation-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            },
            {"title": f"Edit {self.object.variation_number}", "url": None},
        ]

    class UpdateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date_identified"].widget = styled_date_input
            self.fields["attachment"].widget = styled_attachment_input

        class Meta:
            model = ContractVariation
            fields = [
                "title",
                "description",
                "category",
                "variation_type",
                "status",
                "variation_amount",
                "time_extension_days",
                "date_identified",
                "attachment",
                "notes",
            ]

    form_class = UpdateForm

    def get_queryset(self):
        """Filter variations by project."""
        return ContractVariation.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Add success message."""
        messages.success(
            self.request,
            f"Contract Variation '{form.instance.variation_number}' updated successfully!",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to variation list."""
        return reverse(
            "bill_of_quantities:variation-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = False
        return context


class ContractVariationDetailView(ContractVariationMixin, DetailView):
    """View details of a contract variation."""

    model = ContractVariation
    template_name = "contract/variation_detail.html"
    context_object_name = "variation"
    permissions = ["contractor"]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": f"{self.get_project().name} Management",
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.kwargs["project_pk"]},
                ),
            },
            {
                "title": "Contract Variations",
                "url": reverse(
                    "bill_of_quantities:variation-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            },
            {"title": self.object.variation_number, "url": None},
        ]

    def get_queryset(self):
        """Filter variations by project."""
        return ContractVariation.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class ContractVariationDeleteView(ContractVariationMixin, DeleteView):
    """Delete a contract variation."""

    model = ContractVariation
    template_name = "contract/variation_confirm_delete.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": f"{self.get_project().name} Management",
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.kwargs["project_pk"]},
                ),
            },
            {
                "title": "Contract Variations",
                "url": reverse(
                    "bill_of_quantities:variation-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            },
            {"title": f"Delete {self.object.variation_number}", "url": None},
        ]

    model = ContractVariation
    template_name = "contract/variation_confirm_delete.html"
    permissions = ["contractor"]

    def get_queryset(self):
        """Filter variations by project."""
        return ContractVariation.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Soft delete the variation."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(
            self.request,
            f"Contract Variation '{self.object.variation_number}' deleted successfully!",
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to variation list."""
        return reverse(
            "bill_of_quantities:variation-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
