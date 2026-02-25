"""CRUD views for Offsite Log."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import OffsiteLog


class OffsiteLogMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Offsite Log views."""

    model = OffsiteLog
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return OffsiteLog.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Off-Site Log", url=None),
        ]


class OffsiteLogListView(OffsiteLogMixin, ListView):
    """List all offsite logs."""

    template_name = "site_management/offsite_log/list.html"
    context_object_name = "offsite_logs"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class OffsiteLogCreateView(OffsiteLogMixin, CreateView):
    """Create a new offsite log."""

    template_name = "site_management/offsite_log/form.html"
    fields = [
        "date_removed",
        "item_description",
        "quantity",
        "reason_for_removal",
        "removed_by",
        "condition",
        "remarks",
    ]
    widgets = {"date_removed": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date_removed"].widget = self.widgets["date_removed"]
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Off-site log created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:offsite-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class OffsiteLogUpdateView(OffsiteLogMixin, UpdateView):
    """Update an offsite log."""

    template_name = "site_management/offsite_log/form.html"
    fields = [
        "date_removed",
        "item_description",
        "quantity",
        "reason_for_removal",
        "removed_by",
        "condition",
        "remarks",
    ]
    widgets = {"date_removed": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date_removed"].widget = self.widgets["date_removed"]
        return form

    def form_valid(self, form):
        messages.success(self.request, "Off-site log updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:offsite-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class OffsiteLogDeleteView(OffsiteLogMixin, DeleteView):
    """Delete an offsite log."""

    template_name = "site_management/offsite_log/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Off-site log deleted successfully!")
        return reverse_lazy(
            "site_management:offsite-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
