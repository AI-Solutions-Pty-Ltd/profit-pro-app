"""CRUD views for Productivity Log."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import ProductivityLog


class ProductivityLogMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Productivity Log views."""

    model = ProductivityLog
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return ProductivityLog.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Productivity Log", url=None),
        ]


class ProductivityLogListView(ProductivityLogMixin, ListView):
    """List all productivity logs."""

    template_name = "site_management/productivity_log/list.html"
    context_object_name = "productivity_logs"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class ProductivityLogCreateView(ProductivityLogMixin, CreateView):
    """Create a new productivity log."""

    template_name = "site_management/productivity_log/form.html"
    fields = [
        "date",
        "task",
        "crew_size",
        "hours_worked",
        "output",
        "output_unit",
        "remarks",
    ]
    widgets = {"date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Productivity log created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:productivity-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class ProductivityLogUpdateView(ProductivityLogMixin, UpdateView):
    """Update a productivity log."""

    template_name = "site_management/productivity_log/form.html"
    fields = [
        "date",
        "task",
        "crew_size",
        "hours_worked",
        "output",
        "output_unit",
        "remarks",
    ]
    widgets = {"date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        return form

    def form_valid(self, form):
        messages.success(self.request, "Productivity log updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:productivity-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class ProductivityLogDeleteView(ProductivityLogMixin, DeleteView):
    """Delete a productivity log."""

    template_name = "site_management/productivity_log/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Productivity log deleted successfully!")
        return reverse_lazy(
            "site_management:productivity-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
