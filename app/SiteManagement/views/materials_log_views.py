"""CRUD views for Materials Log."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import MaterialsLog


class MaterialsLogMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Materials Log views."""

    model = MaterialsLog
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return MaterialsLog.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Materials Log", url=None),
        ]


class MaterialsLogListView(MaterialsLogMixin, ListView):
    """List all materials logs."""

    template_name = "site_management/materials_log/list.html"
    context_object_name = "materials_logs"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class MaterialsLogCreateView(MaterialsLogMixin, CreateView):
    """Create a new materials log."""

    template_name = "site_management/materials_log/form.html"
    fields = [
        "date_received",
        "supplier",
        "invoice_number",
        "items_received",
        "quantity",
        "unit",
        "intended_usage",
        "comments",
    ]
    widgets = {"date_received": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date_received"].widget = self.widgets["date_received"]
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Materials log created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:materials-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class MaterialsLogUpdateView(MaterialsLogMixin, UpdateView):
    """Update a materials log."""

    template_name = "site_management/materials_log/form.html"
    fields = [
        "date_received",
        "supplier",
        "invoice_number",
        "items_received",
        "quantity",
        "unit",
        "intended_usage",
        "comments",
    ]
    widgets = {"date_received": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date_received"].widget = self.widgets["date_received"]
        return form

    def form_valid(self, form):
        messages.success(self.request, "Materials log updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:materials-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class MaterialsLogDeleteView(MaterialsLogMixin, DeleteView):
    """Delete a materials log."""

    template_name = "site_management/materials_log/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Materials log deleted successfully!")
        return reverse_lazy(
            "site_management:materials-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
