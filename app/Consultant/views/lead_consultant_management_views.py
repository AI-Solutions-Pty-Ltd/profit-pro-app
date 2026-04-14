"""Views for managing Lead Consultant Companies."""

from django.contrib import messages
from django.db.models import QuerySet
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Consultant.views.mixins import LeadConsultantMixin
from app.core.Utilities.mixins import BreadcrumbItem
from app.Project.company.company_forms import CompanyForm
from app.Project.models import Company


class LeadConsultantListView(LeadConsultantMixin, ListView):
    """List all lead consultant companies."""

    model = Company
    template_name = "lead_consultant/lead_consultant_list.html"
    context_object_name = "lead_consultants"

    def get_queryset(self) -> QuerySet[Company]:
        queryset = Company.objects.filter(type=Company.Type.LEAD_CONSULTANT)

        lead_consultant = self.get_project().lead_consultant
        if lead_consultant:
            queryset = queryset.exclude(pk=lead_consultant.pk)

        return queryset.distinct().order_by("name")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(title="Lead Consultants", url=None),
        ]


class LeadConsultantCreateView(LeadConsultantMixin, CreateView):
    """Create a new lead consultant company."""

    model = Company
    form_class = CompanyForm
    template_name = "lead_consultant/lead_consultant_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Lead Consultants",
                url=reverse(
                    "client:lead-consultant-management:lead-consultant-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Add Lead Consultant", url=None),
        ]

    def form_valid(self, form):
        form.instance.type = Company.Type.LEAD_CONSULTANT

        messages.success(self.request, "Lead consultant created successfully.")
        response = super().form_valid(form)
        project = self.get_project()
        project.lead_consultant = self.object
        project.save()
        return response

    def get_success_url(self):
        return reverse_lazy(
            "client:lead-consultant-management:lead-consultant-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class LeadConsultantUpdateView(LeadConsultantMixin, UpdateView):
    """Update a lead consultant company."""

    model = Company
    form_class = CompanyForm
    template_name = "lead_consultant/lead_consultant_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup",
                    kwargs={"pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(
                title="Lead Consultants",
                url=reverse(
                    "client:lead-consultant-management:lead-consultant-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title=f"Edit {self.object.name}", url=None),
        ]

    def form_valid(self, form):
        messages.success(self.request, "Lead consultant updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "client:lead-consultant-management:lead-consultant-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class LeadConsultantDeleteView(LeadConsultantMixin, DeleteView):
    """Delete a lead consultant company."""

    model = Company
    template_name = "lead_consultant/lead_consultant_confirm_delete.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Lead Consultants",
                url=reverse(
                    "client:lead-consultant-management:lead-consultant-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title=f"Delete {self.get_object().name}", url=None),
        ]

    def delete(self, request, *args, **kwargs):
        lead_consultant = self.get_object()
        messages.success(
            request,
            f"Lead consultant '{lead_consultant.name}' deleted successfully.",
        )
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            "client:lead-consultant-management:lead-consultant-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )
