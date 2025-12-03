"""Views for User Management - Clients and Signatories Registers."""

from typing import Any

from django.db.models import Count, QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Client, Project, Signatories


class ClientRegisterView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Client Register - List all clients that can be assigned to projects."""

    model = Client
    template_name = "portfolio/registers/client_register.html"
    context_object_name = "clients"
    permissions = ["consultant", "contractor"]

    def get_breadcrumbs(self: "ClientRegisterView") -> list[BreadcrumbItem]:
        """Return breadcrumbs for client register."""
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-list"),
            ),
            BreadcrumbItem(
                title="User Management",
                url=None,
            ),
            BreadcrumbItem(
                title="Clients Register",
                url=None,
            ),
        ]

    def get_queryset(self: "ClientRegisterView") -> QuerySet[Client]:
        """Get all clients for the user's projects."""
        # Get all projects owned by this user
        user_projects = Project.objects.filter(account=self.request.user)
        # Get clients associated with those projects
        return (
            Client.objects.filter(projects__in=user_projects)
            .distinct()
            .annotate(project_count=Count("projects"))
            .order_by("user__first_name")
        )

    def get_context_data(self: "ClientRegisterView", **kwargs: Any) -> dict[str, Any]:
        """Add additional context for client register."""
        context = super().get_context_data(**kwargs)

        # Get list of projects for each client
        clients_with_projects = []
        for client in context["clients"]:
            projects = Project.objects.filter(account=self.request.user, client=client)
            clients_with_projects.append(
                {
                    "client": client,
                    "projects": projects,
                    "project_count": projects.count(),
                }
            )

        context["clients_data"] = clients_with_projects
        context["total_clients"] = len(clients_with_projects)

        return context


class SignatoriesRegisterView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Signatories Register - List all signatories that can be assigned to projects."""

    model = Signatories
    template_name = "portfolio/registers/signatory_register.html"
    context_object_name = "signatories"
    permissions = ["consultant", "contractor"]

    def get_breadcrumbs(self: "SignatoriesRegisterView") -> list[BreadcrumbItem]:
        """Return breadcrumbs for signatory register."""
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-list"),
            ),
            BreadcrumbItem(
                title="User Management",
                url=None,
            ),
            BreadcrumbItem(
                title="Signatories Register",
                url=None,
            ),
        ]

    def get_queryset(self: "SignatoriesRegisterView") -> QuerySet[Signatories]:
        """Get all signatories for the user's projects."""
        # Get all projects owned by this user
        user_projects = Project.objects.filter(account=self.request.user)
        # Get signatories associated with those projects
        return (
            Signatories.objects.filter(project__in=user_projects)
            .distinct()
            .order_by("user__first_name")
        )

    def get_context_data(
        self: "SignatoriesRegisterView", **kwargs: Any
    ) -> dict[str, Any]:
        """Add additional context for signatory register."""
        context = super().get_context_data(**kwargs)

        # Group signatories by role
        signatories_by_role: dict[str, list[Signatories]] = {}
        for signatory in context["signatories"]:
            role = (
                signatory.get_role_display()
                if hasattr(signatory, "get_role_display")
                else signatory.role
            )
            if role not in signatories_by_role:
                signatories_by_role[role] = []
            signatories_by_role[role].append(signatory)

        context["signatories_by_role"] = signatories_by_role
        context["total_signatories"] = context["signatories"].count()

        return context


class ClientDetailView(UserHasGroupGenericMixin, BreadcrumbMixin, DetailView):
    """Client Detail - Show client with their projects and signatories."""

    model = Client
    template_name = "portfolio/registers/client_detail.html"
    context_object_name = "client"
    permissions = ["consultant", "contractor"]

    def get_breadcrumbs(self: "ClientDetailView") -> list[BreadcrumbItem]:
        """Return breadcrumbs for client detail."""
        client = self.get_object()
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-list"),
            ),
            BreadcrumbItem(
                title="Clients Register",
                url=reverse("project:client-register"),
            ),
            BreadcrumbItem(
                title=client.name,
                url=None,
            ),
        ]

    def get_object(self):
        """Get client and verify user has access."""
        client = get_object_or_404(Client, pk=self.kwargs["pk"])
        # Verify user has access to at least one project with this client
        user_projects = Project.objects.filter(account=self.request.user, client=client)
        if not user_projects.exists():
            from django.http import Http404

            raise Http404("Client not found")
        return client

    def get_context_data(self: "ClientDetailView", **kwargs: Any) -> dict[str, Any]:
        """Add projects and signatories context."""
        context = super().get_context_data(**kwargs)
        client = self.get_object()

        # Get all projects for this client owned by the user
        projects = Project.objects.filter(
            account=self.request.user, client=client
        ).order_by("-created_at")

        # Build project data with signatories
        projects_data = []
        for project in projects:
            signatories = (
                Signatories.objects.filter(project=project)
                .select_related("user")
                .order_by("sequence_number")
            )
            projects_data.append(
                {
                    "project": project,
                    "signatories": signatories,
                    "signatory_count": signatories.count(),
                }
            )

        context["projects_data"] = projects_data
        context["total_projects"] = len(projects_data)

        return context
