"""Views for managing Client Companies."""

from django.contrib import messages
from django.db.models import QuerySet
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms import ClientForm, CompanyForm
from app.Project.models import Company
from app.Project.models.project_roles import Role


class ClientMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for client views."""

    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_queryset(self) -> QuerySet[Company]:
        return Company.objects.filter(type=Company.Type.CLIENT).order_by("name")


class ClientListView(ClientMixin, ListView):
    """List all client companies."""

    model = Company
    template_name = "client/client_list.html"
    context_object_name = "clients"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(title="Clients", url=None),
        ]


class ClientCreateView(ClientMixin, CreateView):
    """Create a new client company."""

    model = Company
    form_class = CompanyForm
    template_name = "client/client_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title="Clients",
                url=reverse("project:client-list"),
            ),
            BreadcrumbItem(title="Add Client", url=None),
        ]

    def get_form_kwargs(self):
        """Pass client=True to form."""
        kwargs = super().get_form_kwargs()
        kwargs["client"] = True
        return kwargs

    def form_valid(self, form):
        form.instance.type = Company.Type.CLIENT
        messages.success(self.request, "Client created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "project:client-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )


class ClientUpdateView(ClientMixin, UpdateView):
    """Update a client company."""

    model = Company
    form_class = ClientForm
    template_name = "client/client_form.html"

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
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(
                title=f"Edit {self.get_object().name}",
                url=None,
            ),
        ]

    def get_form_kwargs(self):
        """Pass client=True to form."""
        kwargs = super().get_form_kwargs()
        kwargs["client"] = True
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Client updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "project:client-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )


class ClientDeleteView(ClientMixin, DeleteView):
    """Delete a client company."""

    model = Company
    template_name = "client/client_confirm_delete.html"

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
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(
                title=f"Delete {self.get_object().name}",
                url=None,
            ),
        ]

    def delete(self, request, *args, **kwargs):
        client = self.get_object()
        messages.success(request, f"Client '{client.name}' deleted successfully.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            "project:client-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )
