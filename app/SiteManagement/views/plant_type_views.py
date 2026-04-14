"""CRUD views for Plant Types."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import PlantType


class PlantTypeMixin(
    SubscriptionRequiredMixin, UserHasProjectRoleGenericMixin, BreadcrumbMixin
):
    """Mixin for Plant Type views."""

    model = PlantType
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"
    required_tiers = [Subscription.SITE_MANAGEMENT]

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return PlantType.objects.filter(project=self.get_project())

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
            BreadcrumbItem(
                title="Plant Types",
                url=str(
                    reverse_lazy(
                        "site_management:plant-type-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
        ]


class PlantTypeListView(PlantTypeMixin, ListView):
    """List all plant types for a project."""

    template_name = "site_management/plant_type/list.html"
    context_object_name = "plant_types"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class PlantTypeCreateView(PlantTypeMixin, CreateView):
    """Create a new plant type."""

    template_name = "site_management/plant_type/form.html"
    fields = ["name", "hourly_rate"]

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Plant Type created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:plant-type-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class PlantTypeUpdateView(PlantTypeMixin, UpdateView):
    """Update an existing plant type."""

    template_name = "site_management/plant_type/form.html"
    fields = ["name", "hourly_rate"]

    def form_valid(self, form):
        messages.success(self.request, "Plant Type updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:plant-type-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class PlantTypeDeleteView(PlantTypeMixin, DeleteView):
    """Delete a plant type."""

    template_name = "site_management/plant_type/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Plant Type deleted successfully!")
        return reverse_lazy(
            "site_management:plant-type-list",
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
