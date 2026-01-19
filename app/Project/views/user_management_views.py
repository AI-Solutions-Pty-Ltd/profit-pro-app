"""Views for User Management - Clients, Signatories, Portfolio & Project Users."""

from typing import Any

from django.contrib import messages
from django.db.models import Count, QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DeleteView, DetailView, ListView
from django.shortcuts import redirect

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Client, Portfolio, Project, Signatories


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
                url=reverse("project:portfolio-dashboard"),
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
        user_projects = Project.objects.filter(users=self.request.user)
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
            projects = Project.objects.filter(users=self.request.user, client=client)
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
                url=reverse("project:portfolio-dashboard"),
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
        user_projects = Project.objects.filter(users=self.request.user)
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
                url=reverse("project:portfolio-dashboard"),
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
        user_projects = Project.objects.filter(users=self.request.user, client=client)
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
            users=self.request.user, client=client
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


# =============================================================================
# Portfolio User Management Views
# =============================================================================


class PortfolioUserListView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """List all users in the current user's portfolio."""

    model = Account
    template_name = "portfolio/registers/portfolio_users.html"
    context_object_name = "portfolio_users"
    permissions = ["consultant", "contractor"]

    def get_portfolio(self) -> Portfolio:
        """Get or create the user's portfolio."""
        user = self.request.user
        if not user.portfolio:  # type: ignore[attr-defined]
            portfolio = Portfolio.objects.create()
            portfolio.users.add(user)  # type: ignore[arg-type]
            user.refresh_from_db()  # type: ignore[attr-defined]
        return user.portfolio  # type: ignore[attr-defined]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(title="User Management", url=None),
            BreadcrumbItem(title="Portfolio Users", url=None),
        ]

    def get_queryset(self) -> QuerySet[Account]:
        """Get all users in the portfolio."""
        portfolio = self.get_portfolio()
        return portfolio.users.all().order_by("first_name", "last_name")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["portfolio"] = self.get_portfolio()
        context["total_users"] = context["portfolio_users"].count()
        return context


class PortfolioUserAddView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Add a user to the portfolio by searching existing users."""

    model = Account
    template_name = "portfolio/registers/portfolio_user_add.html"
    context_object_name = "available_users"
    permissions = ["consultant", "contractor"]

    def get_portfolio(self) -> Portfolio:
        """Get or create the user's portfolio."""
        user = self.request.user
        if not user.portfolio:  # type: ignore[attr-defined]
            portfolio = Portfolio.objects.create()
            portfolio.users.add(user)  # type: ignore[arg-type]
            user.refresh_from_db()  # type: ignore[attr-defined]
        return user.portfolio  # type: ignore[attr-defined]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Portfolio Users", url=reverse("project:portfolio-users")
            ),
            BreadcrumbItem(title="Add User", url=None),
        ]

    def get_queryset(self) -> QuerySet[Account]:
        """Get users not already in the portfolio."""
        portfolio = self.get_portfolio()
        existing_users = portfolio.users.all()
        queryset = Account.objects.exclude(pk__in=existing_users).order_by(
            "first_name", "last_name"
        )

        # Filter by search query if provided
        search = self.request.GET.get("search", "")
        if search:
            queryset = (
                queryset.filter(email__icontains=search)
                | queryset.filter(first_name__icontains=search)
                | queryset.filter(last_name__icontains=search)
            )

        return queryset[:50]  # Limit results

    def post(self, request, *args, **kwargs):
        """Handle adding a user to the portfolio."""
        user_pk = request.POST.get("user_pk")
        if user_pk:
            user_to_add = get_object_or_404(Account, pk=user_pk)
            portfolio = self.get_portfolio()
            portfolio.users.add(user_to_add)
            messages.success(
                request, f"User '{user_to_add.email}' added to portfolio successfully."
            )
        return HttpResponseRedirect(reverse("project:portfolio-users"))

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        return context


class PortfolioUserRemoveView(UserHasGroupGenericMixin, BreadcrumbMixin, DeleteView):
    """Remove a user from the portfolio."""

    model = Account
    template_name = "portfolio/registers/portfolio_user_confirm_remove.html"
    context_object_name = "user_to_remove"
    permissions = ["consultant", "contractor"]

    def get_portfolio(self) -> Portfolio:
        """Get the user's portfolio."""
        return self.request.user.portfolio  # type: ignore[attr-defined]

    def get_object(self) -> Account:
        """Get the user to remove."""
        return get_object_or_404(Account, pk=self.kwargs["user_pk"])

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        user = self.get_object()
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Portfolio Users", url=reverse("project:portfolio-users")
            ),
            BreadcrumbItem(title=f"Remove {user.email}", url=None),
        ]

    def post(self, request, *args, **kwargs):
        """Remove user from portfolio (don't delete the user)."""
        user_to_remove = self.get_object()
        portfolio = self.get_portfolio()

        # Prevent removing yourself
        if user_to_remove == request.user:
            messages.error(request, "You cannot remove yourself from the portfolio.")
            return HttpResponseRedirect(reverse("project:portfolio-users"))

        portfolio.users.remove(user_to_remove)
        messages.success(
            request, f"User '{user_to_remove.email}' removed from portfolio."
        )
        return HttpResponseRedirect(reverse("project:portfolio-users"))


# =============================================================================
# Project User Management Views
# =============================================================================


class ProjectUserListView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """List all users assigned to a project."""

    model = Account
    template_name = "portfolio/registers/project_users.html"
    context_object_name = "project_users"
    permissions = ["consultant", "contractor"]

    def get_project(self) -> Project:
        """Get the project and verify access."""
        return get_object_or_404(Project, pk=self.kwargs["pk"], users=self.request.user)

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=project.name,
                url=reverse("project:project-management", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(title="Project Users", url=None),
        ]

    def get_queryset(self) -> QuerySet[Account]:
        """Get all users assigned to this project."""
        project = self.get_project()
        return project.users.all().order_by("first_name", "last_name")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["total_users"] = context["project_users"].count()
        return context


class ProjectUserDetailView(UserHasGroupGenericMixin, BreadcrumbMixin, DetailView):
    """View details of a user in the context of a project."""

    model = Account
    template_name = "portfolio/registers/project_user_detail.html"
    context_object_name = "user"
    permissions = ["consultant", "contractor"]

    def get_project(self) -> Project:
        """Get the project and verify access."""
        return get_object_or_404(Project, pk=self.kwargs["pk"], users=self.request.user)

    def get_object(self, queryset: QuerySet[Account] | None = None) -> Account:
        """Get the user and verify they're part of the project."""
        project = self.get_project()
        user = get_object_or_404(Account, pk=self.kwargs["user_pk"])
        if user not in project.users.all():
            messages.error(self.request, "User is not assigned to this project.")
            # This will be handled in the get method
        return user

    def get(self, request, *args, **kwargs):
        """Override get to handle redirect if user not in project."""
        self.object = self.get_object()
        project = self.get_project()
        if self.object not in project.users.all():
            return HttpResponseRedirect(
                reverse("project:project-users", kwargs={"pk": project.pk})
            )
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        user = self.get_object()
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=project.name,
                url=reverse("project:project-management", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Project Users",
                url=reverse("project:project-users", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title=f"{user.first_name} {user.last_name}",
                url=None,
            ),
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class ProjectUserAddView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Add a user to a project."""

    model = Account
    template_name = "portfolio/registers/project_user_add.html"
    context_object_name = "available_users"
    permissions = ["consultant", "contractor"]

    def get_project(self) -> Project:
        """Get the project and verify access."""
        return get_object_or_404(Project, pk=self.kwargs["pk"], users=self.request.user)

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=project.name,
                url=reverse("project:project-management", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Project Users",
                url=reverse("project:project-users", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(title="Add User", url=None),
        ]

    def get_queryset(self) -> QuerySet[Account]:
        """Get users not already assigned to this project."""
        project = self.get_project()
        existing_users = project.users.all()
        queryset = Account.objects.exclude(pk__in=existing_users).order_by(
            "first_name", "last_name"
        )

        # Filter by search query if provided
        search = self.request.GET.get("search", "")
        if search:
            queryset = (
                queryset.filter(email__icontains=search)
                | queryset.filter(first_name__icontains=search)
                | queryset.filter(last_name__icontains=search)
            )

        return queryset[:50]  # Limit results

    def post(self: "ProjectUserAddView", request, *args, **kwargs):
        """Handle adding a user to the project."""
        user_pk = request.POST.get("user_pk")
        if user_pk:
            user_to_add = get_object_or_404(Account, pk=user_pk)
            project = self.get_project()
            project.users.add(user_to_add)
            messages.success(
                request,
                f"User '{user_to_add.email}' added to project '{project.name}'.",
            )
        return HttpResponseRedirect(
            reverse("project:project-users", kwargs={"pk": self.get_project().pk})
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["search"] = self.request.GET.get("search", "")
        return context


class ProjectUserRemoveView(UserHasGroupGenericMixin, BreadcrumbMixin, DeleteView):
    """Remove a user from a project."""

    model = Account
    template_name = "portfolio/registers/project_user_confirm_remove.html"
    context_object_name = "user_to_remove"
    permissions = ["consultant", "contractor"]

    def dispatch(self: "ProjectUserRemoveView", request, *args, **kwargs):
        """Dispatch the request."""
        if request.user.pk == self.get_object().pk:
            messages.error(request, "You cannot remove yourself from this project.")
            return redirect("project:project-users", pk=self.get_project().pk)
        return super().dispatch(request, *args, **kwargs)

    def get_project(self) -> Project:
        """Get the project and verify access."""
        return get_object_or_404(Project, pk=self.kwargs["pk"], users=self.request.user)

    def get_object(self) -> Account:
        """Get the user to remove."""
        return get_object_or_404(Account, pk=self.kwargs["user_pk"])

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        user = self.get_object()
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=project.name,
                url=reverse("project:project-management", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Project Users",
                url=reverse("project:project-users", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(title=f"Remove {user.email}", url=None),
        ]

    def post(self, request, *args, **kwargs):
        """Remove user from project (don't delete the user)."""
        user_to_remove = self.get_object()
        project = self.get_project()

        # Check if this is the last user - prevent removing the last user
        if project.users.count() <= 1:
            messages.error(request, "Cannot remove the last user from a project.")
            return HttpResponseRedirect(
                reverse("project:project-users", kwargs={"pk": project.pk})
            )

        project.users.remove(user_to_remove)
        messages.success(
            request,
            f"User '{user_to_remove.email}' removed from project '{project.name}'.",
        )
        return HttpResponseRedirect(
            reverse("project:project-users", kwargs={"pk": project.pk})
        )
