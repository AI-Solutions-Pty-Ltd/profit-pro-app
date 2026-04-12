"""CRUD views for Materials Log."""

from typing import TYPE_CHECKING

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

if TYPE_CHECKING:
    from django.views.generic.edit import FormMixin

    _Base = FormMixin
else:
    _Base = object


from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project, Role
from app.SiteManagement.forms.log_forms import MaterialsLogForm
from app.SiteManagement.models import MaterialsLog


class MaterialsLogMixin(
    _Base,
    SubscriptionRequiredMixin,
    UserHasProjectRoleGenericMixin,
    BreadcrumbMixin,
):
    """Mixin for Materials Log views."""

    model = MaterialsLog
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"
    required_tiers = [Subscription.SITE_MANAGEMENT]
    form_class = MaterialsLogForm

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return MaterialsLog.objects.filter(project=self.get_project())

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
