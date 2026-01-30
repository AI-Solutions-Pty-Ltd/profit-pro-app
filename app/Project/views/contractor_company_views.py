"""Views for managing Contractor Companies."""

from django.contrib import messages
from django.db.models import QuerySet
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms import CompanyForm, ProjectContractorForm
from app.Project.models import Company, Project
from app.Project.models.project_roles import Role


class ContractorMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for contractor views."""

    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_queryset(self) -> QuerySet[Company]:
        return Company.objects.filter(type=Company.Type.CONTRACTOR).order_by("name")


class ContractorListView(ContractorMixin, ListView):
    """List all contractor companies."""

    model = Company
    template_name = "contractor/contractor_list.html"
    context_object_name = "contractors"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(title="Contractors", url=None),
        ]


class ContractorCreateView(ContractorMixin, CreateView):
    """Create a new contractor company."""

    model = Company
    form_class = CompanyForm
    template_name = "contractor/contractor_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title="Contractors",
                url=reverse(
                    "project:contractor-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Add Contractor", url=None),
        ]

    def get_form_kwargs(self):
        """Pass type=CONTRACTOR to form."""
        kwargs = super().get_form_kwargs()
        kwargs["contractor"] = True
        return kwargs

    def form_valid(self, form):
        # Set the type before saving
        form.instance.type = Company.Type.CONTRACTOR
        # Let CreateView handle the save process
        response = super().form_valid(form)
        messages.success(self.request, "Contractor created successfully.")
        return response

    def get_success_url(self):
        return reverse_lazy(
            "project:contractor-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )


class ContractorUpdateView(ContractorMixin, UpdateView):
    """Update a contractor company."""

    model = Company
    form_class = CompanyForm
    template_name = "contractor/contractor_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title="Contractors",
                url=reverse(
                    "project:contractor-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(
                title=f"Edit {self.get_object().name}",
                url=None,
            ),
        ]

    def get_form_kwargs(self):
        """Pass type=CONTRACTOR to form."""
        kwargs = super().get_form_kwargs()
        kwargs["contractor"] = True
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Contractor updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "project:contractor-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )


class ContractorDeleteView(ContractorMixin, DeleteView):
    """Delete a contractor company."""

    model = Company
    template_name = "contractor/contractor_confirm_delete.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio",
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title="Contractors",
                url=reverse(
                    "project:contractor-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(
                title=f"Delete {self.get_object().name}",
                url=None,
            ),
        ]

    def delete(self, request, *args, **kwargs):
        contractor = self.get_object()
        messages.success(
            request, f"Contractor '{contractor.name}' deleted successfully."
        )
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            "project:contractor-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )


class ProjectAllocateContractorView(UserHasProjectRoleGenericMixin, UpdateView):
    """Update the contractor for a project."""

    model = Project
    form_class = ProjectContractorForm
    template_name = "contractor/allocate_contractor_form.html"
    roles = [Role.ADMIN]
    project_slug = "pk"

    def get_object(self: "ProjectAllocateContractorView", queryset=None) -> Project:
        """Get the project from URL."""
        if not queryset:
            queryset = self.get_queryset()
        return self.get_project()

    def get_success_url(self):
        """Redirect to project detail page."""
        return reverse(
            "project:project-edit",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        """Add success message."""
        messages.success(
            self.request, f"Contractor updated successfully for {self.object.name}."
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_contractor_update"] = True
        return context
