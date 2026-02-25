"""CRUD views for Quality Control."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import QualityControl


class QualityControlMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Quality Control views."""

    model = QualityControl
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return QualityControl.objects.filter(project=self.get_project())

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy("project:project-dashboard", kwargs={"pk": project.pk})
                ),
            ),
            BreadcrumbItem(
                title="Site Management",
                url=str(
                    reverse_lazy(
                        "site_management:site-management",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Quality Control", url=None),
        ]


class QualityControlListView(QualityControlMixin, ListView):
    """List all quality control records."""

    template_name = "site_management/quality_control/list.html"
    context_object_name = "quality_controls"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class QualityControlCreateView(QualityControlMixin, CreateView):
    """Create a new quality control record."""

    template_name = "site_management/quality_control/form.html"
    fields = [
        "date",
        "qc_item",
        "area_location",
        "inspector",
        "result",
        "rectification_needed",
        "remarks",
    ]
    widgets = {"date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Quality control record created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:quality-control-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class QualityControlUpdateView(QualityControlMixin, UpdateView):
    """Update a quality control record."""

    template_name = "site_management/quality_control/form.html"
    fields = [
        "date",
        "qc_item",
        "area_location",
        "inspector",
        "result",
        "rectification_needed",
        "remarks",
    ]
    widgets = {"date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        return form

    def form_valid(self, form):
        messages.success(self.request, "Quality control record updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:quality-control-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class QualityControlDeleteView(QualityControlMixin, DeleteView):
    """Delete a quality control record."""

    template_name = "site_management/quality_control/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Quality control record deleted successfully!")
        return reverse_lazy(
            "site_management:quality-control-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
