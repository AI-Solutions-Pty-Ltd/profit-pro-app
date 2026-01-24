"""Views for managing project roles - Contractors, QS, Lead Consultants, Client Reps."""

from typing import Any

from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DeleteView, ListView

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Project, ProjectRole, Role


class BaseRoleListView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Base view for listing users with a specific role in a project."""

    model = Account
    template_name = "project/roles/role_list.html"
    context_object_name = "role_users"
    permissions = ["consultant", "contractor"]
    role: str = ""
    role_display_name: str = ""
    add_url_name: str = ""
    list_url_name: str = ""

    def get_project(self) -> Project:
        """Get the project and verify access."""
        return get_object_or_404(
            Project, pk=self.kwargs["project_pk"], users=self.request.user
        )

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
            BreadcrumbItem(title=self.role_display_name, url=None),
        ]

    def get_queryset(self) -> QuerySet[Account]:
        """Get all users with this role in the project."""
        project = self.get_project()
        project_role = project.project_roles.filter(role=self.role).first()
        if project_role:
            return project_role.users.all().order_by("first_name", "last_name")
        return Account.objects.none()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["role_name"] = self.role_display_name
        context["role_value"] = self.role
        context["total_users"] = context["role_users"].count()
        return context


class BaseRoleAddView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Base view for adding users to a specific role in a project."""

    model = Account
    template_name = "project/roles/role_add.html"
    context_object_name = "available_users"
    permissions = ["consultant", "contractor"]
    role: str = ""
    role_display_name: str = ""
    add_url_name: str = ""
    list_url_name: str = ""

    def get_project(self) -> Project:
        """Get the project and verify access."""
        return get_object_or_404(
            Project, pk=self.kwargs["project_pk"], users=self.request.user
        )

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
            BreadcrumbItem(title=f"Add {self.role_display_name}", url=None),
        ]

    def get_queryset(self) -> QuerySet[Account]:
        """Get users not already in this role."""
        project = self.get_project()
        project_role = project.project_roles.filter(role=self.role).first()

        if project_role:
            existing_users = project_role.users.all()
            queryset = Account.objects.exclude(pk__in=existing_users)
        else:
            queryset = Account.objects.all()

        queryset = queryset.order_by("first_name", "last_name")

        # Filter by search query if provided
        search = self.request.GET.get("search", "")
        if search:
            queryset = (
                queryset.filter(email__icontains=search)
                | queryset.filter(first_name__icontains=search)
                | queryset.filter(last_name__icontains=search)
            )

        return queryset[:50]

    def post(self, request, *args, **kwargs):
        """Handle adding a user to this role."""
        user_pk = request.POST.get("user_pk")
        if user_pk:
            user_to_add = get_object_or_404(Account, pk=user_pk)
            project = self.get_project()

            # Get or create the ProjectRole
            project_role, created = ProjectRole.objects.get_or_create(
                project=project,
                role=self.role,
            )

            # Add user to this role
            project_role.users.add(user_to_add)
            # Also add to project.users M2M for access
            project.users.add(user_to_add)

            messages.success(
                request,
                f"Added '{user_to_add.email}' as {self.role_display_name}.",
            )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        raise NotImplementedError("Subclasses must implement get_success_url")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["role_name"] = self.role_display_name
        context["search"] = self.request.GET.get("search", "")
        return context


class BaseRoleRemoveView(UserHasGroupGenericMixin, BreadcrumbMixin, DeleteView):
    """Base view for removing users from a specific role in a project."""

    model = Account
    template_name = "project/roles/role_confirm_remove.html"
    context_object_name = "user_to_remove"
    permissions = ["consultant", "contractor"]
    role: str = ""
    role_display_name: str = ""
    add_url_name: str = ""
    list_url_name: str = ""

    def get_project(self) -> Project:
        """Get the project and verify access."""
        return get_object_or_404(
            Project, pk=self.kwargs["project_pk"], users=self.request.user
        )

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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["role_name"] = self.role_display_name
        return context

    def post(self, request, *args, **kwargs):
        """Remove user from this role."""
        user_to_remove = self.get_object()
        project = self.get_project()

        project_role = project.project_roles.filter(role=self.role).first()
        if project_role:
            project_role.users.remove(user_to_remove)
            messages.success(
                request,
                f"Removed '{user_to_remove.email}' from {self.role_display_name}.",
            )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        raise NotImplementedError("Subclasses must implement get_success_url")


# =============================================================================
# Contractor Views
# =============================================================================


class ContractorListView(BaseRoleListView):
    """List contractors for a project."""

    role = Role.CONTRACT_BOQ
    role_display_name = "Contractors"


class ContractorAddView(BaseRoleAddView):
    """Add a contractor to a project."""

    role = Role.CONTRACT_BOQ
    role_display_name = "Contractor"

    def get_success_url(self):
        return reverse(
            "project:project-contractors",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class ContractorRemoveView(BaseRoleRemoveView):
    """Remove a contractor from a project."""

    role = Role.CONTRACT_BOQ
    role_display_name = "Contractor"

    def get_success_url(self):
        return reverse(
            "project:project-contractors",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


# =============================================================================
# Quantity Surveyor Views
# =============================================================================


class QuantitySurveyorListView(BaseRoleListView):
    """List quantity surveyors for a project."""

    role = Role.COST_FORECASTS
    role_display_name = "Quantity Surveyors"


class QuantitySurveyorAddView(BaseRoleAddView):
    """Add a quantity surveyor to a project."""

    role = Role.COST_FORECASTS
    role_display_name = "Quantity Surveyor"

    def get_success_url(self):
        return reverse(
            "project:project-quantity-surveyors",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class QuantitySurveyorRemoveView(BaseRoleRemoveView):
    """Remove a quantity surveyor from a project."""

    role = Role.COST_FORECASTS
    role_display_name = "Quantity Surveyor"

    def get_success_url(self):
        return reverse(
            "project:project-quantity-surveyors",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


# =============================================================================
# Lead Consultant Views
# =============================================================================


class LeadConsultantListView(BaseRoleListView):
    """List lead consultants for a project."""

    role = Role.PORTFOLIO_MANAGER
    role_display_name = "Lead Consultants"


class LeadConsultantAddView(BaseRoleAddView):
    """Add a lead consultant to a project."""

    role = Role.PORTFOLIO_MANAGER
    role_display_name = "Lead Consultant"

    def get_success_url(self):
        return reverse(
            "project:project-lead-consultants",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class LeadConsultantRemoveView(BaseRoleRemoveView):
    """Remove a lead consultant from a project."""

    role = Role.PORTFOLIO_MANAGER
    role_display_name = "Lead Consultant"

    def get_success_url(self):
        return reverse(
            "project:project-lead-consultants",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


# =============================================================================
# Client Representative Views
# =============================================================================


class ClientRepresentativeListView(BaseRoleListView):
    """List client representatives for a project."""

    role = Role.PORTFOLIO_USER
    role_display_name = "Client Representatives"


class ClientRepresentativeAddView(BaseRoleAddView):
    """Add a client representative to a project."""

    role = Role.PORTFOLIO_USER
    role_display_name = "Client Representative"

    def get_success_url(self):
        return reverse(
            "project:project-client-representatives",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class ClientRepresentativeRemoveView(BaseRoleRemoveView):
    """Remove a client representative from a project."""

    role = Role.PORTFOLIO_USER
    role_display_name = "Client Representative"

    def get_success_url(self):
        return reverse(
            "project:project-client-representatives",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )
