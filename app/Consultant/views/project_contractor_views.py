"""Views for managing Contractor Companies."""

from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import View
from django.views.generic.edit import FormView

from app.Consultant.views.mixins import ContractorMixin
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms import ProjectContractorForm
from app.Project.models import Role


class ContractorRemoveForm(forms.Form):
    """Simple form for contractor removal confirmation."""

    pass


class ProjectAllocateExistingContractorView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, FormView
):
    """Allocate a contractor to a project."""

    form_class = ProjectContractorForm
    template_name = "contractor/allocate_contractor_form.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_initial(self):
        """Set initial value for the contractor field."""
        return {"contractor": self.project.contractor}

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title="Contractors",
                url=reverse(
                    "client:contractor-management:contractor-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Allocate Contractor", url=None),
        ]

    def get_form_kwargs(self):
        """Pass the project to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Save the selected contractor to the project."""
        contractor = form.cleaned_data["contractor"]
        project = self.get_project()
        project.contractor = contractor
        project.save()

        if contractor:
            messages.success(
                self.request,
                f"Contractor '{contractor.name}' has been allocated to project '{project.name}'.",
            )
        else:
            messages.info(
                self.request,
                f"Contractor has been removed from project '{project.name}'.",
            )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to project edit page."""
        return reverse_lazy(
            "client:contractor-management:contractor-list",
            kwargs={"project_pk": self.project.pk},
        )


class ProjectContractorRemoveView(ContractorMixin, View):
    """Remove contractor from project."""

    template_name = "contractor/contractor_confirm_remove.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title="Contractors",
                url=reverse(
                    "client:contractor-management:contractor-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(
                title=f"Remove Contractor {self.project.contractor.name}",
                url=None,
            ),
        ]

    def dispatch(self, request, *args, **kwargs):
        """Get the contractor and verify project ownership."""
        # Verify that the user owns the project associated with this contractor
        self.project = self.get_project()
        self.contractor = self.get_contractor("contractor_pk")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Display the confirmation page."""
        return render(
            request,
            self.template_name,
            {
                "project": self.project,
                "contractor": self.contractor,
                "breadcrumbs": self.get_breadcrumbs(),
            },
        )

    def post(self, request, *args, **kwargs):
        """Remove the contractor from the project."""
        if self.project.contractor == self.contractor:
            contractor_name = self.contractor.name
            self.project.contractor = None
            self.project.save()
            messages.success(
                request,
                f"Contractor '{contractor_name}' has been removed from project '{self.project.name}'.",
            )
        else:
            messages.warning(
                request, "This contractor is not assigned to this project."
            )

        return redirect(
            "client:contractor-management:contractor-list", project_pk=self.project.pk
        )
