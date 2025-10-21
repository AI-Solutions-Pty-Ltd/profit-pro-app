"""Views for managing Project signatories."""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import SignatoryForm
from app.Project.models import Project, Signatories


class SignatoryMixin(UserHasGroupGenericMixin):
    """Mixin for signatory views."""

    permissions = ["contractor"]

    def get_project(self):
        """Get the project for the current view."""
        if not hasattr(self, "project"):
            self.project = get_object_or_404(
                Project,
                pk=self.kwargs["project_pk"],
                account=self.request.user,
            )
        return self.project

    def get_queryset(self):
        """Filter signatories by project."""
        project = self.get_project()
        return Signatories.objects.filter(
            project=project, project__account=self.request.user
        ).order_by("-created_at")

    def get_object(self):
        """Get signatory and verify project ownership."""
        signatory = super().get_object()
        if signatory.project.account != self.request.user:
            raise Http404("You do not have permission to view this signatory.")
        return signatory


class SignatoryListView(SignatoryMixin, ListView):
    """List all signatories for a project."""

    model = Signatories
    template_name = "signatory/signatory_list.html"
    context_object_name = "signatories"

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SignatoryCreateView(SignatoryMixin, CreateView):
    """Create a new signatory for a project."""

    model = Signatories
    form_class = SignatoryForm
    template_name = "signatory/signatory_form.html"

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self, form):
        """Set the project before saving."""
        form.instance.project = self.get_project()
        messages.success(
            self.request,
            f"Signatory '{form.instance.name}' has been added successfully.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the signatory list."""
        return reverse_lazy(
            "project:signatory-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )


class SignatoryUpdateView(SignatoryMixin, UpdateView):
    """Update an existing signatory."""

    model = Signatories
    form_class = SignatoryForm
    template_name = "signatory/signatory_form.html"

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self, form):
        """Show success message."""
        messages.success(
            self.request,
            f"Signatory '{form.instance.name}' has been updated successfully.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the signatory list."""
        return reverse_lazy(
            "project:signatory-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )


class SignatoryDeleteView(SignatoryMixin, DeleteView):
    """Delete a signatory."""

    model = Signatories
    template_name = "signatory/signatory_confirm_delete.html"

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self, form):
        """Soft delete the signatory."""
        signatory = self.get_object()
        signatory.soft_delete()
        messages.success(
            self.request, f"Signatory '{signatory.name}' has been deleted successfully."
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to the signatory list."""
        return reverse_lazy(
            "project:signatory-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )
