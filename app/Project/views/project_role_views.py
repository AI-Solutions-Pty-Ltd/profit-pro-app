"""Views for managing project roles (contractors, quantity surveyors, lead consultants, client representatives)."""

from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import DeleteView, ListView
from django.contrib import messages
from django.shortcuts import redirect

from app.Account.models import Account
from app.Project.models import Project

User = get_user_model()

if TYPE_CHECKING:
    from django.http import HttpRequest


class ProjectRoleMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user has access to project."""

    request: "HttpRequest"
    kwargs: dict[str, Any]

    def test_func(self) -> bool:
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return False

        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])

        # Check if user is in project users or is superuser
        # Type ignore because AbstractBaseUser doesn't have is_superuser at type level
        if hasattr(user, "is_superuser") and user.is_superuser:  # type: ignore[attr-defined]
            return True

        # Check if user is in the many-to-many relationship
        project_users: QuerySet[Account] = project.users.all()
        # Type ignore because "in" operator checking is complex for Django users
        return user in project_users  # type: ignore[operator]

    def get_project(self) -> Project:
        """Get the project object."""
        return get_object_or_404(Project, pk=self.kwargs["project_pk"])


class ProjectRoleListView(ProjectRoleMixin, ListView):
    """Base view for listing users in a specific role."""

    model = Account
    template_name = "project/roles/role_list.html"
    context_object_name = "role_users"
    paginate_by = 50

    # These will be defined in subclasses
    role_field: str
    role_name: str
    role_name_plural: str
    url_name: str

    def get_queryset(self):
        """Get users for the specific role."""
        project = self.get_project()
        role_field = self.role_field
        return getattr(project, role_field).all()

    def get_context_data(self, **kwargs):
        """Add project and role information to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["role_name"] = self.role_name
        context["role_name_plural"] = self.role_name_plural
        context["add_url"] = reverse_lazy(
            f"project:{self.url_name}-add", kwargs={"project_pk": self.get_project().pk}
        )
        return context


class ProjectRoleAddView(ProjectRoleMixin, ListView):
    """Base view for adding users to a specific role."""

    model = Account
    template_name = "project/roles/role_add.html"
    context_object_name = "available_users"
    paginate_by = 50

    # These will be defined in subclasses
    role_field: str
    role_name: str
    role_name_plural: str
    url_name: str

    def get_queryset(self):
        """Get users not already in the role."""
        project = self.get_project()
        role_field = self.role_field
        current_users = getattr(project, role_field).all()
        return Account.objects.exclude(id__in=current_users).order_by(
            "first_name", "last_name"
        )

    def get_context_data(self, **kwargs):
        """Add project and role information to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["role_name"] = self.role_name
        context["role_name_plural"] = self.role_name_plural
        context["list_url"] = reverse_lazy(
            f"project:{self.url_name}", kwargs={"project_pk": self.get_project().pk}
        )
        return context


class ProjectRoleRemoveView(ProjectRoleMixin, DeleteView):
    """Base view for removing a user from a specific role."""

    model = Account
    template_name = "project/roles/role_confirm_remove.html"
    context_object_name = "role_user"

    # These will be defined in subclasses
    role_field: str
    role_name: str
    url_name: str

    def dispatch(self: "ProjectRoleRemoveView", request, *args, **kwargs):
        """Dispatch the request."""
        if request.user.pk == self.kwargs["user_pk"]:
            messages.error(request, "You cannot remove yourself from this role.")
            return redirect("project:project-users", project_pk=self.get_project().pk)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        """Get the user to be removed."""
        return get_object_or_404(Account, pk=self.kwargs["user_pk"])

    def get_context_data(self, **kwargs):
        """Add project and role information to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["role_name"] = self.role_name
        return context

    def delete(self, request, *args, **kwargs):
        """Remove user from the role."""
        project = self.get_project()
        user = self.get_object()
        role_field = self.role_field
        getattr(project, role_field).remove(user)
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        """Redirect to role list after removal."""
        return reverse_lazy(
            f"project:{self.url_name}", kwargs={"project_pk": self.get_project().pk}
        )


# Concrete views for each role
class ContractorListView(ProjectRoleListView):
    """List all contractors for the project."""

    role_field = "contractors"
    role_name = "Contractor"
    role_name_plural = "Contractors"
    url_name = "project-contractors"


class ContractorAddView(ProjectRoleAddView):
    """Add contractors to the project."""

    role_field = "contractors"
    role_name = "Contractor"
    role_name_plural = "Contractors"
    url_name = "project-contractors"

    def post(self, request, *args, **kwargs):
        """Add selected users to contractors."""
        project = self.get_project()
        user_ids = request.POST.getlist("users")
        users = Account.objects.filter(id__in=user_ids)
        project.contractors.add(*users)
        return self.get_success_url()

    def get_success_url(self):
        """Redirect to contractor list after adding."""
        return reverse_lazy(
            "project:project-contractors", kwargs={"project_pk": self.get_project().pk}
        )


class ContractorRemoveView(ProjectRoleRemoveView):
    """Remove a contractor from the project."""

    role_field = "contractors"
    role_name = "Contractor"
    url_name = "project-contractors"


class QuantitySurveyorListView(ProjectRoleListView):
    """List all quantity surveyors for the project."""

    role_field = "quantity_surveyors"
    role_name = "Quantity Surveyor"
    role_name_plural = "Quantity Surveyors"
    url_name = "project-quantity-surveyors"


class QuantitySurveyorAddView(ProjectRoleAddView):
    """Add quantity surveyors to the project."""

    role_field = "quantity_surveyors"
    role_name = "Quantity Surveyor"
    role_name_plural = "Quantity Surveyors"
    url_name = "project-quantity-surveyors"

    def post(self, request, *args, **kwargs):
        """Add selected users to quantity surveyors."""
        project = self.get_project()
        user_ids = request.POST.getlist("users")
        users = Account.objects.filter(id__in=user_ids)
        project.quantity_surveyors.add(*users)
        return self.get_success_url()

    def get_success_url(self):
        """Redirect to quantity surveyor list after adding."""
        return reverse_lazy(
            "project:project-quantity-surveyors",
            kwargs={"project_pk": self.get_project().pk},
        )


class QuantitySurveyorRemoveView(ProjectRoleRemoveView):
    """Remove a quantity surveyor from the project."""

    role_field = "quantity_surveyors"
    role_name = "Quantity Surveyor"
    url_name = "project-quantity-surveyors"


class LeadConsultantListView(ProjectRoleListView):
    """List all lead consultants for the project."""

    role_field = "lead_consultants"
    role_name = "Lead Consultant"
    role_name_plural = "Lead Consultants"
    url_name = "project-lead-consultants"


class LeadConsultantAddView(ProjectRoleAddView):
    """Add lead consultants to the project."""

    role_field = "lead_consultants"
    role_name = "Lead Consultant"
    role_name_plural = "Lead Consultants"
    url_name = "project-lead-consultants"

    def post(self, request, *args, **kwargs):
        """Add selected users to lead consultants."""
        project = self.get_project()
        user_ids = request.POST.getlist("users")
        users = Account.objects.filter(id__in=user_ids)
        project.lead_consultants.add(*users)
        return self.get_success_url()

    def get_success_url(self):
        """Redirect to lead consultant list after adding."""
        return reverse_lazy(
            "project:project-lead-consultants",
            kwargs={"project_pk": self.get_project().pk},
        )


class LeadConsultantRemoveView(ProjectRoleRemoveView):
    """Remove a lead consultant from the project."""

    role_field = "lead_consultants"
    role_name = "Lead Consultant"
    url_name = "project-lead-consultants"


class ClientRepresentativeListView(ProjectRoleListView):
    """List all client representatives for the project."""

    role_field = "client_representatives"
    role_name = "Client Representative"
    role_name_plural = "Client Representatives"
    url_name = "project-client-representatives"


class ClientRepresentativeAddView(ProjectRoleAddView):
    """Add client representatives to the project."""

    role_field = "client_representatives"
    role_name = "Client Representative"
    role_name_plural = "Client Representatives"
    url_name = "project-client-representatives"

    def post(self, request, *args, **kwargs):
        """Add selected users to client representatives."""
        project = self.get_project()
        user_ids = request.POST.getlist("users")
        users = Account.objects.filter(id__in=user_ids)
        project.client_representatives.add(*users)
        return self.get_success_url()

    def get_success_url(self):
        """Redirect to client representative list after adding."""
        return reverse_lazy(
            "project:project-client-representatives",
            kwargs={"project_pk": self.get_project().pk},
        )


class ClientRepresentativeRemoveView(ProjectRoleRemoveView):
    """Remove a client representative from the project."""

    role_field = "client_representatives"
    role_name = "Client Representative"
    url_name = "project-client-representatives"
