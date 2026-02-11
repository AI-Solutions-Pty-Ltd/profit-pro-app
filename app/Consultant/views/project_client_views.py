"""Views for managing Client Companies."""

from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import View
from django.views.generic.edit import FormView

from app.Consultant.forms import ProjectClientForm
from app.Consultant.views.mixins import ClientMixin
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Role


class ClientRemoveForm(forms.Form):
    """Simple form for client removal confirmation."""

    pass


class ProjectAllocateExistingClientView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, FormView
):
    """Allocate a client to a project."""

    form_class = ProjectClientForm
    template_name = "client/allocate_client_form.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_initial(self):
        """Set initial value for the client field."""
        return {"client": self.project.client}

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-edit", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title="Clients",
                url=reverse(
                    "client:client-management:client-list",
                    kwargs={"project_pk": self.project.pk},
                ),
            ),
            BreadcrumbItem(title="Allocate Client", url=None),
        ]

    def form_valid(self, form):
        """Save the selected client to the project."""
        client = form.cleaned_data["client"]
        project = self.get_project()
        project.client = client
        project.save()

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
        return reverse_lazy(
            "client:client-management:client-list",
            kwargs={"project_pk": self.project.pk},
        )


class ProjectClientRemoveView(ClientMixin, View):
    """Remove client from project."""

    template_name = "client/client_confirm_remove.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-edit", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title="Clients",
                url=reverse(
                    "client:client-management:client-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(
                title=f"Remove Client {self.project.client.name}",
                url=None,
            ),
        ]

    def dispatch(self, request, *args, **kwargs):
        """Get the client and verify project ownership."""
        # Verify that the user owns the project associated with this client
        self.project = self.get_project()
        self.client = self.get_client("client_pk")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Display the confirmation page."""
        return render(
            request,
            self.template_name,
            {
                "project": self.project,
                "client": self.client,
                "breadcrumbs": self.get_breadcrumbs(),
            },
        )

    def post(self, request, *args, **kwargs):
        """Remove the client from the project."""
        if self.project.client == self.client:
            client_name = self.client.name
            self.project.client = None
            self.project.save()
            messages.success(
                request,
                f"Client '{client_name}' has been removed from project '{self.project.name}'.",
            )
        else:
            messages.warning(request, "This client is not assigned to this project.")

        return redirect(
            "client:client-management:client-list", project_pk=self.project.pk
        )
