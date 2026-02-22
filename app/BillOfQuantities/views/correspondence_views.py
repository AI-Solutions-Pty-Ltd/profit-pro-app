"""Views for managing contract variations and correspondence."""

from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.BillOfQuantities.forms.correspondence_forms import CorrespondenceDialogForm
from app.BillOfQuantities.models import ContractualCorrespondence
from app.BillOfQuantities.models.contract_models import CorrespondenceDialogFile
from app.core.Utilities.forms import styled_attachment_input, styled_date_input
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Role

# =============================================================================
# Contractual Correspondence Views
# =============================================================================


class CorrespondenceMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for correspondence views."""

    roles = [Role.CORRESPONDENCE, Role.ADMIN, Role.USER]
    project_slug = "project_pk"


class CorrespondenceListView(CorrespondenceMixin, ListView):
    """List all correspondences for a project."""

    model = ContractualCorrespondence
    template_name = "contract/correspondence_list.html"
    context_object_name = "correspondences"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": f"{self.get_project().name} Management",
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.kwargs["project_pk"]},
                ),
            },
            {"title": "Correspondences", "url": None},
        ]

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
                "title": "Correspondences",
                "url": reverse(
                    "bill_of_quantities:correspondence-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            },
            {"title": "Create Correspondence", "url": None},
        ]

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
                "title": "Correspondences",
                "url": reverse(
                    "bill_of_quantities:correspondence-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            },
            {"title": f"Edit {self.object.reference_number}", "url": None},
        ]

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
                "title": "Correspondences",
                "url": reverse(
                    "bill_of_quantities:correspondence-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            },
            {"title": self.object.reference_number, "url": None},
        ]

    def get_queryset(self):
        """Filter correspondences by project."""
        return ContractualCorrespondence.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def get_context_data(self, **kwargs):
        """Add project and form to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["form"] = CorrespondenceDialogForm()
        return context


class CorrespondenceDeleteView(CorrespondenceMixin, DeleteView):
    """Delete a correspondence."""

    model = ContractualCorrespondence
    template_name = "contract/correspondence_confirm_delete.html"

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
                "title": "Correspondences",
                "url": reverse(
                    "bill_of_quantities:correspondence-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            },
            {"title": f"Delete {self.object.reference_number}", "url": None},
        ]

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


class CorrespondenceDialog(CorrespondenceMixin, View):
    """Handle correspondence dialog creation with file attachments."""

    def post(self, request, project_pk, pk, *args, **kwargs):
        project = self.get_project()
        correspondence = get_object_or_404(
            ContractualCorrespondence, pk=pk, project=project
        )

        if not correspondence.sender_user:
            correspondence.sender_user = request.user
            correspondence.save()
            correspondence.refresh_from_db()

        form = CorrespondenceDialogForm(data=request.POST, files=request.FILES)

        if form.is_valid():
            dialog = form.save(commit=False)
            dialog.correspondence = correspondence
            dialog.sender_user = request.user
            if request.user == correspondence.recipient_user:
                dialog.recipient = correspondence.sender
                dialog.receiver_user = correspondence.sender_user
            else:
                dialog.recipient = correspondence.recipient
                dialog.receiver_user = correspondence.recipient_user
            dialog.save()

            # Form already handles attachments if commit=True
            # But we saved with commit=False, so handle them manually
            attachments = form.cleaned_data.get("attachments", [])
            for file in attachments:
                if file:
                    CorrespondenceDialogFile.objects.create(dialog=dialog, file=file)

            messages.success(request, "Message sent successfully!")
        else:
            messages.error(request, "Please correct the errors below.")

        return redirect(
            "bill_of_quantities:correspondence-detail", project_pk=project.pk, pk=pk
        )
