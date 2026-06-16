"""Views for managing Project Consultant allocations."""

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import View
from django.views.generic.edit import FormView

from app.Consultant.views.mixins import LeadConsultantMixin
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms.forms import ProjectConsultantForm, ProjectLeadConsultantForm
from app.Project.models import Company, Role


class ProjectAllocateLeadConsultantView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, FormView
):
    """Allocate a lead consultant to a project."""

    form_class = ProjectLeadConsultantForm
    template_name = "lead_consultant/allocate_lead_consultant_form.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title="Lead Consultants",
                url=reverse(
                    "client:lead-consultant-management:lead-consultant-list",
                    kwargs={"project_pk": self.project.pk},
                ),
            ),
            BreadcrumbItem(title="Allocate Lead Consultant", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_lead_consultants"] = Company.objects.filter(
            type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT]
        ).exists()
        return context

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

        if lead_consultant:
            lead_consultant.type = form.cleaned_data["type"]
            lead_consultant.save()
            project.consultants.add(lead_consultant)
            messages.success(
                self.request,
                f"Lead Consultant '{lead_consultant.name}' has been allocated to project '{project.name}'.",
            )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to project edit page."""
        return reverse_lazy(
            "project:project-setup",
            kwargs={"pk": self.project.pk},
        )


class ProjectAllocateConsultantView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, FormView
):
    """Allocate a regular consultant to a project."""

    form_class = ProjectConsultantForm
    template_name = "lead_consultant/allocate_consultant_form.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title="Consultants",
                url=reverse(
                    "client:lead-consultant-management:lead-consultant-list",
                    kwargs={"project_pk": self.project.pk},
                ),
            ),
            BreadcrumbItem(title="Allocate Consultant", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_consultants"] = Company.objects.filter(
            type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT]
        ).exists()
        return context

    def get_form_kwargs(self):
        """Pass the project to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Save the selected consultant to the project."""
        consultant = form.cleaned_data["consultant"]
        project = self.get_project()

        if consultant:
            consultant.type = form.cleaned_data["type"]
            consultant.save()
            project.consultants.add(consultant)
            messages.success(
                self.request,
                f"Consultant '{consultant.name}' has been allocated to project '{project.name}'.",
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
                url=None,
            ),
            BreadcrumbItem(
                title=f"Remove Lead Consultant {self.lead_consultant.name}",
                url=None,
            ),
        ]

    def dispatch(self, request, *args, **kwargs):
        """Get the lead consultant and verify project ownership."""
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
        if self.lead_consultant in self.project.consultants.all():
            lead_consultant_name = self.lead_consultant.name
            self.project.consultants.remove(self.lead_consultant)
            messages.success(
                request,
                f"Lead Consultant '{lead_consultant_name}' has been removed from project '{self.project.name}'.",
            )
        else:
            messages.warning(
                request, "This lead consultant is not assigned to this project."
            )

        return redirect("project:project-setup", pk=self.project.pk)


class ProjectConsultantRemoveView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, View
):
    """Remove regular consultant from project."""

    template_name = "lead_consultant/consultant_confirm_remove.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title="Consultants",
                url=None,
            ),
            BreadcrumbItem(
                title=f"Remove Consultant {self.consultant.name}",
                url=None,
            ),
        ]

    def dispatch(self, request, *args, **kwargs):
        """Get the consultant and verify project ownership."""
        self.project = self.get_project()
        self.consultant = get_object_or_404(
            Company, id=kwargs["consultant_pk"], type=Company.Type.CONSULTANT
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Display the confirmation page."""
        return render(
            request,
            self.template_name,
            {
                "project": self.project,
                "consultant": self.consultant,
                "breadcrumbs": self.get_breadcrumbs(),
            },
        )

    def post(self, request, *args, **kwargs):
        """Remove the consultant from the project."""
        if self.consultant in self.project.consultants.all():
            consultant_name = self.consultant.name
            self.project.consultants.remove(self.consultant)
            messages.success(
                request,
                f"Consultant '{consultant_name}' has been removed from project '{self.project.name}'.",
            )
        else:
            messages.warning(
                request, "This consultant is not assigned to this project."
            )

        return redirect("project:project-setup", pk=self.project.pk)
