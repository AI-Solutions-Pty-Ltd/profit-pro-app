"""Views for Claim management."""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.BillOfQuantities.forms import ClaimForm
from app.BillOfQuantities.models import Claim
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Role


class ClaimMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Base mixin for claim views."""

    roles = [Role.CLAIMS]
    project_slug = "project_pk"
    model = Claim

    def get_queryset(self):
        """Filter claims by project."""
        return Claim.objects.filter(project=self.get_project()).order_by("-period")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb trail."""
        project = self.get_project()
        return [
            {
                "title": "Projects",
                "url": str(
                    reverse_lazy(
                        "project:project-management", kwargs={"pk": project.pk}
                    )
                ),
            },
            {"title": project.name, "url": str(project.get_absolute_url())},
            {"title": "Claims", "url": None},
        ]


class ClaimListView(ClaimMixin, ListView):
    """List all claims for a project."""

    template_name = "claims/claim_list.html"
    context_object_name = "claims"
    paginate_by = 10


class ClaimCreateView(ClaimMixin, CreateView):
    """Create a new claim."""

    template_name = "claims/claim_form.html"
    form_class = ClaimForm
    success_url = None

    def dispatch(self, request, *args, **kwargs):
        """Check if project has required dates before proceeding."""
        project = self.get_project()
        if not project.start_date or not project.end_date:
            messages.error(
                self.request,
                "Project must have both start date and end date before creating claims.",
            )
            return redirect("project:project-management", pk=project.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["title"] = "Create Claim"
        return context

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

    def get_initial(self):
        """Set initial value for project."""
        initial = super().get_initial()
        initial["project"] = self.get_project()
        return initial

    def form_valid(self, form):
        """Set project and save claim."""
        form.instance.project = self.get_project()
        messages.success(self.request, "Claim created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to claim list."""
        return reverse_lazy(
            "bill_of_quantities:claim-list",
            kwargs={"project_pk": self.get_project().pk},
        )


class ClaimUpdateView(ClaimMixin, UpdateView):
    """Update an existing claim."""

    template_name = "claims/claim_form.html"
    form_class = ClaimForm

    def dispatch(self, request, *args, **kwargs):
        """Check if project has required dates before proceeding."""
        project = self.get_project()
        if not project.start_date or not project.end_date:
            messages.error(
                self.request,
                "Project must have both start date and end date before updating claims.",
            )
            return redirect("project:project-detail", pk=project.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["title"] = "Update Claim"
        return context

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

    def form_valid(self, form):
        """Save updated claim."""
        messages.success(self.request, "Claim updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to claim list."""
        return reverse_lazy(
            "bill_of_quantities:claim-list",
            kwargs={"project_pk": self.get_project().pk},
        )


class ClaimDeleteView(ClaimMixin, DeleteView):
    """Delete a claim."""

    template_name = "claims/claim_confirm_delete.html"

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def delete(self, request, *args, **kwargs):
        """Delete claim with success message."""
        messages.success(request, "Claim deleted successfully!")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        """Redirect to claim list."""
        return reverse_lazy(
            "bill_of_quantities:claim-list",
            kwargs={"project_pk": self.get_project().pk},
        )
