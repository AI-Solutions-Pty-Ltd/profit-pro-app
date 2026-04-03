"""Views for managing Lead Consultant Companies."""

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import View
from django.views.generic.edit import FormView

from app.Consultant.views.mixins import LeadConsultantMixin
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms.forms import ProjectLeadConsultantForm
from app.Project.models import Role


class ProjectAllocateLeadConsultantView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, FormView
):
    """Allocate a lead consultant to a project."""

    form_class = ProjectLeadConsultantForm
    template_name = "lead_consultant/allocate_lead_consultant_form.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_initial(self):
        """Set initial value for the lead consultant field."""
        return {"lead_consultant": self.project.lead_consultant}

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title="Lead Consultants",
                url=None,  # Update this when lead consultant list view exists
            ),
            BreadcrumbItem(title="Allocate Lead Consultant", url=None),
        ]

    def get_form_kwargs(self):
        """Pass the project to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Save the selected lead consultant to the project."""
        lead_consultant = form.cleaned_data["lead_consultant"]
        project = self.get_project()
        project.lead_consultant = lead_consultant
        project.save()

        if lead_consultant:
            messages.success(
                self.request,
                f"Lead Consultant '{lead_consultant.name}' has been allocated to project '{project.name}'.",
            )
        else:
            messages.info(
                self.request,
                f"Lead Consultant has been removed from project '{project.name}'.",
            )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to project edit page."""
        return reverse_lazy(
            "project:project-setup",
            kwargs={"pk": self.project.pk},
        )


class ProjectLeadConsultantRemoveView(LeadConsultantMixin, View):
    """Remove lead consultant from project."""

    template_name = "lead_consultant/lead_consultant_confirm_remove.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title="Lead Consultants",
                url=None,  # Update this when a lead consultant list view exists
            ),
            BreadcrumbItem(
                title=f"Remove Lead Consultant {self.project.lead_consultant.name}",
                url=None,
            ),
        ]

    def dispatch(self, request, *args, **kwargs):
        """Get the lead consultant and verify project ownership."""
        # Verify that the user owns the project associated with this lead consultant
        self.project = self.get_project()
        self.lead_consultant = self.get_lead_consultant("lead_consultant_pk")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Display the confirmation page."""
        return render(
            request,
            self.template_name,
            {
                "project": self.project,
                "lead_consultant": self.lead_consultant,
                "breadcrumbs": self.get_breadcrumbs(),
            },
        )

    def post(self, request, *args, **kwargs):
        """Remove the lead consultant from the project."""
        if self.project.lead_consultant == self.lead_consultant:
            lead_consultant_name = self.lead_consultant.name
            self.project.lead_consultant = None
            self.project.save()
            messages.success(
                request,
                f"Lead Consultant '{lead_consultant_name}' has been removed from project '{self.project.name}'.",
            )
        else:
            messages.warning(
                request, "This lead consultant is not assigned to this project."
            )

        return redirect("project:project-setup", pk=self.project.pk)
