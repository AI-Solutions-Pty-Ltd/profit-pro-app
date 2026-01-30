"""View for allocating a client to a project."""

from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms import ProjectClientForm
from app.Project.models import Project
from app.Project.models.project_roles import Role


class ProjectAllocateClientView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, UpdateView
):
    """Allocate a client to a project."""

    model = Project
    form_class = ProjectClientForm
    template_name = "client/allocate_client_form.html"
    roles = [Role.ADMIN]
    project_slug = "pk"

    def get_initial(self):
        """Set initial value for the client field."""
        return {"client": self.object.client}

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title="Clients",
                url=reverse(
                    "project:client-list",
                    kwargs={"project_pk": self.kwargs["pk"]},
                ),
            ),
            BreadcrumbItem(title="Allocate Client", url=None),
        ]

    def form_valid(self, form):
        """Save the selected client to the project."""
        client = form.cleaned_data["client"]
        self.object.client = client
        self.object.save()

        if client:
            messages.success(
                self.request,
                f"Client '{client.name}' has been allocated to the project.",
            )
        else:
            messages.info(self.request, "Client has been removed from the project.")

        # Don't call super().form_valid() since form is not a ModelForm
        # Instead, redirect directly to success URL
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to project edit page."""
        return reverse_lazy("project:project-edit", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
