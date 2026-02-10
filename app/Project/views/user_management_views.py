"""Views for User Management - Clients, Signatories, Portfolio & Project Users."""

from typing import Any

from django.contrib import messages
from django.db import models
from django.db.models import Count, QuerySet
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DeleteView, DetailView, FormView, ListView

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import (
    UserHasGroupGenericMixin,
    UserHasProjectRoleGenericMixin,
)
from app.Project.forms import ProjectUserCreateForm
from app.Project.models import Company, Project, ProjectRole, Role, Signatories

# Import the task
from app.Project.tasks import send_project_user_welcome_email


class ClientRegisterView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Client Register - List all clients that can be assigned to projects."""

    model = Company
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

    def get_queryset(self: "ClientRegisterView") -> QuerySet[Company]:
        """Get all clients for the user's projects."""
        # Get all projects owned by this user
        return (
            Company.objects.filter(type=Company.Type.CLIENT)
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


class ClientDetailView(UserHasGroupGenericMixin, BreadcrumbMixin, DetailView):
    """Client Detail - Show client with their projects and signatories."""

    model = Company
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

    def get_object(
        self, queryset: models.query.QuerySet[Company] | None = None
    ) -> Company:
        """Get client and verify user has access."""
        client = get_object_or_404(
            Company, type=Company.Type.CLIENT, pk=self.kwargs["pk"]
        )
        # Verify user has access to at least one project with this client
        user_projects = Project.objects.filter(client=client)
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
# Project User/Role Management Views
# =============================================================================


class ProjectUserListView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, ListView):
    """List all users and their roles assigned to a project."""

    model = Account
    template_name = "portfolio/registers/project_users.html"
    context_object_name = "project_users"
    roles = [Role.ADMIN]
    project_slug = "pk"

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
            BreadcrumbItem(title="Project Users & Roles", url=None),
        ]

    def get_queryset(self) -> QuerySet[Account]:
        """Get all unique users with roles in this project."""
        project = self.get_project()
        # Get all users who have at least one role in this project
        users_with_roles = (
            Account.objects.filter(project_roles__project=project)
            .distinct()
            .order_by("first_name", "last_name")
        )
        return users_with_roles

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project
        context["available_roles"] = Role.choices

        # Get roles for each user
        user_roles = {}
        for user in context["project_users"]:
            user_roles[user.pk] = project.project_roles.filter(user=user).values_list(
                "role", flat=True
            )

        context["user_roles"] = user_roles
        context["total_users"] = context["project_users"].count()
        return context


class ProjectUserDetailView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, DetailView
):
    """View and edit a user's roles in the context of a project."""

    model = Account
    template_name = "portfolio/registers/project_user_detail.html"
    context_object_name = "user"
    roles = [Role.ADMIN]
    project_slug = "pk"

    def get_project(self) -> Project:
        """Get the project and verify access."""
        return get_object_or_404(Project, pk=self.kwargs["pk"], users=self.request.user)

    def get_object(self, queryset: QuerySet[Account] | None = None) -> Account:
        """Get the user."""
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
                title="Project Users & Roles",
                url=reverse("project:project-users", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title=f"{user.first_name} {user.last_name}",
                url=None,
            ),
        ]

    def post(self, request, *args, **kwargs):
        """Handle updating user roles."""
        project = self.get_project()
        user = self.get_object()
        selected_roles = request.POST.getlist("roles")

        # Get current roles for this user
        current_roles = set(
            project.project_roles.filter(user=user).values_list("role", flat=True)
        )
        new_roles = set(selected_roles)

        # Roles to add
        for role_value in new_roles - current_roles:
            ProjectRole.objects.create(project=project, role=role_value, user=user)

        # Roles to remove
        for role_value in current_roles - new_roles:
            project.project_roles.filter(role=role_value, user=user).delete()

        messages.success(request, f"Roles updated for {user.email}.")
        return HttpResponseRedirect(
            reverse(
                "project:project-user-detail",
                kwargs={"pk": project.pk, "user_pk": user.pk},
            )
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        user = self.get_object()
        context["project"] = project
        # Get all available roles
        context["available_roles"] = Role.choices
        # Get role values this user has in this project
        context["user_role_values"] = list(
            project.project_roles.filter(user=user).values_list("role", flat=True)
        )
        return context


class ProjectUserAddView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, ListView):
    """Add a user to a project with a specific role."""

    model = Account
    template_name = "portfolio/registers/project_user_add.html"
    context_object_name = "available_users"
    roles = [Role.ADMIN]
    project_slug = "pk"

    def get_project(self) -> Project:
        """Get the project and verify access."""
        user: Account = self.request.user  # type: ignore
        project = Project.objects.get(pk=self.kwargs["pk"])
        if not project.users.filter(pk=user.pk).exists():
            messages.error(self.request, "User does not have access to this project")
            raise Http404("User does not have access to this project")
        return project

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
                title="Project Users & Roles",
                url=reverse("project:project-users", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(title="Add User", url=None),
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project
        context["search"] = self.request.GET.get("search", "")
        return context

    def get_queryset(self) -> QuerySet[Account]:
        """Get all users (can add same user with different roles)."""
        queryset = Account.objects.all().order_by("first_name", "last_name")

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
        """Handle adding a user to the project - redirects to detail page for role assignment."""
        user_pk = request.POST.get("user_pk")

        if user_pk:
            user_to_add = get_object_or_404(Account, pk=user_pk)
            project = self.get_project()

            # Check if user already in project
            if user_to_add in project.users.all():
                messages.info(
                    request,
                    f"'{user_to_add.email}' is already in this project. Manage their roles below.",
                )
            else:
                # Add to project.users M2M for access
                project.users.add(user_to_add)
                messages.success(
                    request,
                    f"'{user_to_add.email}' added to project. Assign roles below.",
                )

            # Redirect to detail page for role management
            return HttpResponseRedirect(
                reverse(
                    "project:project-user-detail",
                    kwargs={"pk": project.pk, "user_pk": user_to_add.pk},
                )
            )
        else:
            messages.error(request, "Please select a user.")
            return redirect("project:project-user-add", pk=self.get_project().pk)


class ProjectUserCreateView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, FormView):
    """Create a new user and add them to the project."""

    form_class = ProjectUserCreateForm
    template_name = "portfolio/registers/project_user_create.html"
    roles = [Role.ADMIN]

    def get_project(self) -> Project:
        """Get the project and verify access."""
        user: Account = self.request.user  # type: ignore
        project = Project.objects.get(pk=self.kwargs["pk"])
        if not project.users.filter(pk=user.pk).exists():
            messages.error(self.request, "User does not have access to this project")
            raise Http404("User does not have access to this project")
        return project

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title="Projects",
                url=reverse("project:project-management", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Project Users",
                url=reverse("project:project-users", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Create User",
                url=None,
            ),
        ]

    def get_initial(self) -> dict[str, Any]:
        """Pre-populate email from query parameter."""
        initial = super().get_initial()
        email = self.request.GET.get("email", "")
        if email:
            initial["email"] = email
        return initial

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self, form):
        """Create the user and send welcome email."""
        project = self.get_project()
        email = form.cleaned_data["email"]
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data.get("last_name", "")

        # Create user account with unusable password
        user = Account.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_unusable_password()
        user.save()

        # Add user to project without roles
        project.users.add(user)
        project.save()

        # Send welcome email using the task
        email_sent = send_project_user_welcome_email(
            user=user,
            project_name=project.name,
            request_domain=self.request.get_host(),
            request_protocol="https" if self.request.is_secure() else "http",
        )

        if email_sent:
            messages.success(
                self.request,
                f"User '{user.email}' has been created and added to the project. "
                f"A welcome email with setup instructions has been sent.",
            )
        else:
            messages.warning(
                self.request,
                f"User '{user.email}' has been created and added to the project, "
                f"but the welcome email could not be sent.",
            )

        return redirect("project:project-user-detail", pk=project.pk, user_pk=user.pk)

    def form_invalid(self, form):
        """Handle form submission errors."""
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class ProjectUserRemoveView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, DeleteView
):
    """Remove a user from a project role."""

    model = Account
    template_name = "portfolio/registers/project_user_confirm_remove.html"
    context_object_name = "user_to_remove"
    roles = [Role.ADMIN]

    def dispatch(self: "ProjectUserRemoveView", request, *args, **kwargs):
        """Dispatch the request."""
        if request.user.pk == self.kwargs.get("user_pk"):
            messages.error(request, "You cannot remove yourself from this project.")
            return redirect("project:project-users", pk=self.get_project().pk)
        return super().dispatch(request, *args, **kwargs)

    def get_project(self) -> Project:
        """Get the project and verify access."""
        return get_object_or_404(Project, pk=self.kwargs["pk"], users=self.request.user)

    def get_object(
        self, queryset: models.query.QuerySet[Account] | None = None
    ) -> Account:
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
                title="Project Users & Roles",
                url=reverse("project:project-users", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(title=f"Remove {user.email}", url=None),
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        user = self.get_object()
        context["project"] = project
        # Get all roles this user has in this project
        context["user_roles"] = project.project_roles.filter(user=user)
        return context

    def post(self, request, *args, **kwargs):
        """Remove user from project roles."""
        user_to_remove = self.get_object()
        project = self.get_project()

        # Get the role to remove (if specified) or remove from all roles
        role_to_remove = request.POST.get("role")

        if role_to_remove:
            # Remove from specific role
            project.project_roles.filter(
                role=role_to_remove, user=user_to_remove
            ).delete()
            messages.success(
                request,
                f"Removed '{role_to_remove}' role from '{user_to_remove.email}'.",
            )
        else:
            # Remove from all roles
            project.project_roles.filter(user=user_to_remove).delete()

            # Also remove from project.users M2M
            project.users.remove(user_to_remove)
            messages.success(
                request,
                f"User '{user_to_remove.email}' removed from project '{project.name}'.",
            )

        return HttpResponseRedirect(
            reverse("project:project-users", kwargs={"pk": project.pk})
        )
