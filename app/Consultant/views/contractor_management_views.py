"""Views for managing Contractor Companies."""

from django.contrib import messages
from django.db.models import QuerySet
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Account.models import Account
from app.Consultant.views.mixins import ContractorMixin
from app.core.Utilities.mixins import BreadcrumbItem
from app.Project.forms import CompanyForm
from app.Project.models import Company


class ContractorListView(ContractorMixin, ListView):
    """List all contractor companies."""

    model = Company
    template_name = "contractor/contractor_list.html"
    context_object_name = "contractors"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-edit", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(title="Contractors", url=None),
        ]

    def get_queryset(self) -> QuerySet[Company]:
        user: Account = self.request.user  # type: ignore
        projects = user.get_projects
        return Company.objects.filter(
            contractor_projects__in=projects, type=Company.Type.CONTRACTOR
        ).order_by("name")


class ContractorCreateView(ContractorMixin, CreateView):
    """Create a new contractor company."""

    model = Company
    form_class = CompanyForm
    template_name = "contractor/contractor_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-edit", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Contractors",
                url=reverse(
                    "client:contractor-management:contractor-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Add Contractor", url=None),
        ]

    def form_valid(self, form):
        form.instance.type = Company.Type.CONTRACTOR

        messages.success(self.request, "Contractor created successfully.")
        response = super().form_valid(form)
        project = self.get_project()
        project.contractor = self.object
        project.save()
        return response

    def get_success_url(self):
        return reverse_lazy(
            "client:contractor-management:contractor-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class ContractorUpdateView(ContractorMixin, UpdateView):
    """Update a contractor company."""

    model = Company
    form_class = CompanyForm
    template_name = "contractor/contractor_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-edit",
                    kwargs={"pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(
                title="Contractors",
                url=reverse(
                    "client:contractor-management:contractor-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(
                title=f"Edit {self.object.name}",
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
            "client:contractor-management:contractor-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class ContractorDeleteView(ContractorMixin, DeleteView):
    """Delete a contractor company."""

    model = Company
    template_name = "contractor/contractor_confirm_delete.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse("project:portfolio-dashboard"),
            ),
            BreadcrumbItem(
                title="Contractors",
                url=reverse(
                    "client:contractor-management:contractor-list",
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
            "client:contractor-management:contractor-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )
