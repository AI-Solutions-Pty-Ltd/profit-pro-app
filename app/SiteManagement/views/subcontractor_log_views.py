"""CRUD views for Subcontractor Log."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project, Role, SubcontractorEntity
from app.SiteManagement.models import SubcontractorLog


class SubcontractorLogMixin(
    SubscriptionRequiredMixin, UserHasProjectRoleGenericMixin, BreadcrumbMixin
):
    """Mixin for Subcontractor Log views."""

    model = SubcontractorLog
    required_tiers = [Subscription.SITE_MANAGEMENT]
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return SubcontractorLog.objects.filter(project=self.get_project())

    def get_form(self, form_class=None):
        """Filter subcontractor_entity and apply date widgets."""
        form = super().get_form(form_class)
        project = self.get_project()
        if "subcontractor_entity" in form.fields:
            form.fields["subcontractor_entity"].queryset = (
                SubcontractorEntity.objects.filter(project=project)
            )

        # Apply date widgets
        date_fields = ["date", "start_date", "planned_finish_date", "actual_finish_date"]
        for field_name in date_fields:
            if field_name in form.fields:
                form.fields[field_name].widget = DateInput(attrs={"type": "date"})
        return form

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
            BreadcrumbItem(title="Subcontractor Log", url=None),
        ]


class SubcontractorLogListView(SubcontractorLogMixin, ListView):
    """List all subcontractor logs."""

    template_name = "site_management/subcontractor_log/list.html"
    context_object_name = "subcontractor_logs"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SubcontractorLogCreateView(SubcontractorLogMixin, CreateView):
    """Create a new subcontractor log."""

    template_name = "site_management/subcontractor_log/form.html"
    fields = [
        "subcontractor_entity",
        "date",
        "task",
        "hours_worked",
        "output",
        "output_unit",
        "remarks",
    ]

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Subcontractor log created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:subcontractor-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SubcontractorLogUpdateView(SubcontractorLogMixin, UpdateView):
    """Update a labour log."""

    template_name = "site_management/subcontractor_log/form.html"
    fields = [
        "subcontractor_entity",
        "date",
        "task",
        "hours_worked",
        "output",
        "output_unit",
        "remarks",
    ]

    def form_valid(self, form):
        messages.success(self.request, "Subcontractor log updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:subcontractor-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SubcontractorLogDeleteView(SubcontractorLogMixin, DeleteView):
    """Delete a subcontractor log."""

    template_name = "site_management/subcontractor_log/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Subcontractor log deleted successfully!")
        return reverse_lazy(
            "site_management:subcontractor-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
