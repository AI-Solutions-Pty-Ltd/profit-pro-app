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
    ContractualCorrespondence,
    ContractVariation,
)
from app.core.Utilities.forms import styled_attachment_input, styled_date_input
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models.project_roles import Role


class ContractVariationMixin(UserHasProjectRoleGenericMixin):
    """Mixin for contract variation views."""

    project_slug = "project_pk"


class ContractVariationListView(ContractVariationMixin, ListView):
    """List all contract variations for a project."""

    model = ContractVariation
    template_name = "contract/variation_list.html"
    context_object_name = "variations"
    roles = [Role.CONTRACT_VARIATIONS, Role.ADMIN, Role.USER]
    project_slug = "project_pk"

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


# =============================================================================
# Contractual Correspondence Views
# =============================================================================


class CorrespondenceMixin(UserHasProjectRoleGenericMixin):
    """Mixin for correspondence views."""

    roles = [Role.CORRESPONDENCE, Role.ADMIN, Role.USER]
    project_slug = "project_pk"


class CorrespondenceListView(CorrespondenceMixin, ListView):
    """List all correspondences for a project."""

    model = ContractualCorrespondence
    template_name = "contract/correspondence_list.html"
    context_object_name = "correspondences"

    def get_queryset(self):
        """Filter correspondences by project."""
        return ContractualCorrespondence.objects.filter(
            project=self.get_project(),
            deleted=False,
        ).order_by("-date_of_correspondence")

    def get_context_data(self, **kwargs):
        """Add project and summary stats to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        # Summary statistics
        correspondences = self.get_queryset()
        context["total_count"] = correspondences.count()
        context["incoming_count"] = correspondences.filter(
            direction=ContractualCorrespondence.Direction.INCOMING
        ).count()
        context["outgoing_count"] = correspondences.filter(
            direction=ContractualCorrespondence.Direction.OUTGOING
        ).count()
        context["pending_response_count"] = correspondences.filter(
            requires_response=True,
            response_sent=False,
        ).count()

        return context


class CorrespondenceCreateView(CorrespondenceMixin, CreateView):
    """Create a new correspondence."""

    model = ContractualCorrespondence
    template_name = "contract/correspondence_form.html"

    def get_form_class(self):
        """Return the form class for this view."""
        return self.CreateForm

    class CreateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date_of_correspondence"].widget = styled_date_input
            self.fields["response_due_date"].widget = styled_date_input
            self.fields["attachment"].widget = styled_attachment_input

        class Meta:
            model = ContractualCorrespondence
            fields = [
                "reference_number",
                "subject",
                "correspondence_type",
                "direction",
                "date_of_correspondence",
                "sender",
                "recipient",
                "summary",
                "requires_response",
                "response_due_date",
                "attachment",
            ]

    def form_valid(self, form):
        """Set project and logged_by before saving."""
        form.instance.project = self.get_project()
        form.instance.logged_by = self.request.user
        messages.success(
            self.request,
            f"Correspondence '{form.instance.reference_number}' created successfully!",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to correspondence list."""
        return reverse(
            "bill_of_quantities:correspondence-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = True
        return context


class CorrespondenceUpdateView(CorrespondenceMixin, UpdateView):
    """Update an existing correspondence."""

    model = ContractualCorrespondence
    template_name = "contract/correspondence_form.html"

    def get_form_class(self):
        """Return the form class for this view."""
        return self.UpdateForm

    class UpdateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date_of_correspondence"].widget = styled_date_input
            self.fields["response_due_date"].widget = styled_date_input
            self.fields["response_date"].widget = styled_date_input
            self.fields["attachment"].widget = styled_attachment_input

        class Meta:
            model = ContractualCorrespondence
            fields = [
                "reference_number",
                "subject",
                "correspondence_type",
                "direction",
                "date_of_correspondence",
                "sender",
                "recipient",
                "summary",
                "requires_response",
                "response_due_date",
                "response_sent",
                "response_date",
                "attachment",
            ]

    def get_queryset(self):
        """Filter correspondences by project."""
        return ContractualCorrespondence.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Add success message."""
        messages.success(
            self.request,
            f"Correspondence '{form.instance.reference_number}' updated successfully!",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to correspondence list."""
        return reverse(
            "bill_of_quantities:correspondence-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = False
        return context


class CorrespondenceDetailView(CorrespondenceMixin, DetailView):
    """View details of a correspondence."""

    model = ContractualCorrespondence
    template_name = "contract/correspondence_detail.html"
    context_object_name = "correspondence"

    def get_queryset(self):
        """Filter correspondences by project."""
        return ContractualCorrespondence.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class CorrespondenceDeleteView(CorrespondenceMixin, DeleteView):
    """Delete a correspondence."""

    model = ContractualCorrespondence
    template_name = "contract/correspondence_confirm_delete.html"

    def get_queryset(self):
        """Filter correspondences by project."""
        return ContractualCorrespondence.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Soft delete the correspondence."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(
            self.request,
            f"Correspondence '{self.object.reference_number}' deleted successfully!",
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to correspondence list."""
        return reverse(
            "bill_of_quantities:correspondence-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
