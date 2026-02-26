"""CRUD views for Request for Information (RFI)."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models.rfi import RFI


class RFIMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for RFI views."""

    model = RFI
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return RFI.objects.filter(project=self.get_project()).select_related(
            "issued_by", "to_user"
        )


class RFIListView(RFIMixin, ListView):
    """List all RFIs for a project."""

    template_name = "site_management/rfi/list.html"
    context_object_name = "rfis"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["open_count"] = self.get_queryset().filter(status="OPEN").count()
        context["closed_count"] = self.get_queryset().filter(status="CLOSED").count()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Requests for Information", url=None),
        ]


class RFIDetailView(RFIMixin, DetailView):
    """View details of an RFI."""

    template_name = "site_management/rfi/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Requests for Information",
                url=str(
                    reverse_lazy(
                        "site_management:rfi-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=self.get_object().reference_number, url=None),
        ]


class RFICreateView(RFIMixin, CreateView):
    """Create a new RFI."""

    template_name = "site_management/rfi/form.html"
    fields = [
        "to_user",
        "subject",
        "message",
        "respond_by_date",
        "attachment",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["respond_by_date"].widget = DateInput(attrs={"type": "date"})
        form.fields["to_user"].queryset = Account.objects.filter(
            project_roles__project=self.get_project()
        ).distinct()
        form.fields["to_user"].label = "To"
        form.fields["subject"].widget.attrs["placeholder"] = (
            "Brief subject of this request"
        )
        form.fields["message"].widget.attrs["placeholder"] = (
            "Detailed description or question requiring a response"
        )
        return form

    def form_valid(self, form):
        project = self.get_project()
        form.instance.project = project
        form.instance.issued_by = self.request.user
        messages.success(self.request, "RFI submitted successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:rfi-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Requests for Information",
                url=str(
                    reverse_lazy(
                        "site_management:rfi-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Create RFI", url=None),
        ]


class RFIUpdateView(RFIMixin, UpdateView):
    """Update an RFI (edit details or add response)."""

    template_name = "site_management/rfi/form.html"
    fields = [
        "to_user",
        "subject",
        "message",
        "respond_by_date",
        "attachment",
        "response",
        "response_attachment",
        "status",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["respond_by_date"].widget = DateInput(attrs={"type": "date"})
        form.fields["to_user"].queryset = Account.objects.filter(
            project_roles__project=self.get_project()
        ).distinct()
        form.fields["to_user"].label = "To"
        form.fields["subject"].widget.attrs["placeholder"] = (
            "Brief subject of this request"
        )
        form.fields["message"].widget.attrs["placeholder"] = (
            "Detailed description or question requiring a response"
        )
        form.fields["response"].widget.attrs["placeholder"] = "Response to this RFI"
        return form

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.response and not obj.response_date:
            obj.response_date = timezone.now().date()
        if obj.status == "CLOSED" and not obj.date_closed:
            obj.date_closed = timezone.now().date()
        elif obj.status == "OPEN":
            obj.date_closed = None
        obj.save()
        messages.success(self.request, "RFI updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:rfi-detail",
            kwargs={"project_pk": self.get_project().pk, "pk": self.object.pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Requests for Information",
                url=str(
                    reverse_lazy(
                        "site_management:rfi-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=self.get_object().reference_number, url=None),
        ]


class RFIDeleteView(RFIMixin, DeleteView):
    """Delete an RFI."""

    template_name = "site_management/rfi/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "RFI deleted successfully.")
        return reverse_lazy(
            "site_management:rfi-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
