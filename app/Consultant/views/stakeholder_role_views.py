from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import FormView, UpdateView, DeleteView
from app.Consultant.forms import ProjectCompanyUserRoleForm
from app.Project.models import Company, Project, ProjectCompanyUserRole, Role
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin


class ProjectCompanyUserRoleAllocateView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, FormView
):
    """Allocate a user to a company on a project with a role."""

    form_class = ProjectCompanyUserRoleForm
    template_name = "stakeholder_role/allocate_user_role_form.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_project()
        self.company = get_object_or_404(Company, pk=kwargs["company_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["company"] = self.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["company"] = self.company
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title=f"Allocate User - {self.company.name}",
                url=None,
            ),
        ]

    def form_valid(self, form):
        user_role = form.save(commit=False)
        user_role.project = self.project
        user_role.company = self.company

        # Validate unique constraint before saving to avoid database integrity errors breaking the transaction
        if ProjectCompanyUserRole.objects.filter(
            project=self.project,
            company=self.company,
            user=user_role.user
        ).exists():
            form.add_error("user", f"User '{user_role.user}' is already assigned a role for this company on this project.")
            messages.error(
                self.request,
                f"User '{user_role.user}' is already assigned a role for this company on this project.",
            )
            return self.form_invalid(form)

        user_role.save()
        messages.success(
            self.request,
            f"User '{user_role.user}' assigned as {user_role.role} for {self.company.name} successfully.",
        )
        return redirect("project:project-setup", pk=self.project.pk)


class ProjectCompanyUserRoleUpdateView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, UpdateView
):
    """Update stakeholder role for a user."""

    model = ProjectCompanyUserRole
    form_class = ProjectCompanyUserRoleForm
    template_name = "stakeholder_role/allocate_user_role_form.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_project()
        self.company = get_object_or_404(Company, pk=kwargs["company_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["company"] = self.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["company"] = self.company
        context["is_update"] = True
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title=f"Edit Role - {self.get_object().user}",
                url=None,
            ),
        ]

    def form_valid(self, form):
        user_role = form.save()
        messages.success(
            self.request,
            f"Updated role for '{user_role.user}' to {user_role.role} successfully.",
        )
        return redirect("project:project-setup", pk=self.project.pk)


class ProjectCompanyUserRoleRemoveView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, DeleteView
):
    """Remove user stakeholder role assignment."""

    model = ProjectCompanyUserRole
    template_name = "stakeholder_role/confirm_remove_user_role.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_project()
        self.company = get_object_or_404(Company, pk=kwargs["company_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["company"] = self.company
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title=f"Remove User Role - {self.get_object().user}",
                url=None,
            ),
        ]

    def get_success_url(self):
        messages.success(
            self.request, "User stakeholder assignment removed successfully."
        )
        return reverse("project:project-setup", kwargs={"pk": self.project.pk})
