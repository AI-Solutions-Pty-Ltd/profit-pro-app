"""CRUD views for Labour Log."""

from typing import TYPE_CHECKING

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

if TYPE_CHECKING:
    from django.views.generic.edit import FormMixin

    _Base = FormMixin
else:

    class _Base:
        pass


from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project, Role
from app.SiteManagement.forms.log_forms import LabourLogForm
from app.SiteManagement.models import LabourLog


class LabourLogMixin(
    _Base,
    SubscriptionRequiredMixin,
    UserHasProjectRoleGenericMixin,
    BreadcrumbMixin,
):
    """Mixin for Labour Log views."""

    model = LabourLog
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"
    required_tiers = [Subscription.SITE_MANAGEMENT]
    form_class = LabourLogForm

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return LabourLog.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Labour Log", url=None),
        ]


class LabourLogListView(LabourLogMixin, ListView):
    """List all labour logs."""

    template_name = "site_management/labour_log/list.html"
    context_object_name = "labour_logs"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class LabourLogCreateView(LabourLogMixin, CreateView):
    """Create a new labour log."""

    template_name = "site_management/labour_log/form.html"

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Labour log created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:labour-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class LabourLogUpdateView(LabourLogMixin, UpdateView):
    """Update a labour log."""

    template_name = "site_management/labour_log/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Labour log updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:labour-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class LabourLogDeleteView(LabourLogMixin, DeleteView):
    """Delete a labour log."""

    template_name = "site_management/labour_log/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Labour log deleted successfully!")
        return reverse_lazy(
            "site_management:labour-log-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def post(self, request, *args, **kwargs):
        """Override post to call delete directly, bypassing form validation."""
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Soft delete the object and redirect."""
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.soft_delete()
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
