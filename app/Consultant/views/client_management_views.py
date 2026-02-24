"""Views for managing Client Companies."""

from django.contrib import messages
from django.db.models import QuerySet
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
)

from app.Account.models import Account
from app.Consultant.views.mixins import ClientMixin
from app.core.Utilities.mixins import BreadcrumbItem
from app.Project.forms import ClientForm
from app.Project.models import Company


class ClientListView(ClientMixin, ListView):
    """List all client companies."""

    model = Company
    template_name = "client/client_list.html"
    context_object_name = "clients"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(title="Clients", url=None),
        ]

    def get_queryset(self) -> QuerySet[Company]:
        user: Account = self.request.user  # type: ignore
        projects = user.get_projects
        project = self.get_project()
        queryset = (
            Company.objects.filter(
                client_projects__in=projects, type=Company.Type.CLIENT
            )
            .distinct()
            .order_by("name")
        )

        # Exclude the currently assigned client
        if project.client:
            queryset = queryset.exclude(pk=project.client.pk)

        return queryset


class ClientCreateView(ClientMixin, CreateView):
    """Create a new client company."""

    model = Company
    form_class = ClientForm
    template_name = "client/client_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Clients",
                url=reverse(
                    "client:client-management:client-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Add Client", url=None),
        ]

    def form_valid(self, form):
        form.instance.type = Company.Type.CLIENT

        messages.success(self.request, "Client created successfully.")
        response = super().form_valid(form)
        project = self.get_project()
        project.client = self.object
        project.save()
        return response

    def get_success_url(self):
        return reverse_lazy(
            "client:client-management:client-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class ClientUpdateView(ClientMixin, UpdateView):
    """Update a client company."""

    model = Company
    form_class = ClientForm
    template_name = "client/client_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup",
                    kwargs={"pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(
                title="Clients",
                url=reverse(
                    "client:client-management:client-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(
                title=f"Edit {self.object.name}",
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
            "client:client-management:client-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )
