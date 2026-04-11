"""CRUD views for Subcontractor Log."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project, Role
from app.SiteManagement.forms.log_forms import SubcontractorLogForm
from app.SiteManagement.models import SubcontractorLog


class SubcontractorLogMixin(
    SubscriptionRequiredMixin, UserHasProjectRoleGenericMixin, BreadcrumbMixin
):
    """Mixin for Subcontractor Log views."""

    model = SubcontractorLog
    required_tiers = [Subscription.SITE_MANAGEMENT]
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"
    form_class = SubcontractorLogForm

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return SubcontractorLog.objects.filter(project=self.get_project())

    def get_form_kwargs(self):
        """Pass the project to the form for queryset filtering."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

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
