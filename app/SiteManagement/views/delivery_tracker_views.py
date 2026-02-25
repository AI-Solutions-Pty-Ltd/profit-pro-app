"""CRUD views for Delivery Tracker."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import DeliveryTracker


class DeliveryTrackerMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Delivery Tracker views."""

    model = DeliveryTracker
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return DeliveryTracker.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Delivery Tracker", url=None),
        ]


class DeliveryTrackerListView(DeliveryTrackerMixin, ListView):
    """List all delivery trackers."""

    template_name = "site_management/delivery_tracker/list.html"
    context_object_name = "delivery_trackers"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class DeliveryTrackerCreateView(DeliveryTrackerMixin, CreateView):
    """Create a new delivery tracker."""

    template_name = "site_management/delivery_tracker/form.html"
    fields = [
        "item",
        "supplier",
        "ordered_date",
        "expected_delivery_date",
        "actual_delivery_date",
        "delivered_quantity",
        "remarks",
    ]
    widgets = {
        "ordered_date": DateInput(attrs={"type": "date"}),
        "expected_delivery_date": DateInput(attrs={"type": "date"}),
        "actual_delivery_date": DateInput(attrs={"type": "date"}),
    }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, widget in self.widgets.items():
            form.fields[field_name].widget = widget
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Delivery tracker created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:delivery-tracker-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class DeliveryTrackerUpdateView(DeliveryTrackerMixin, UpdateView):
    """Update a delivery tracker."""

    template_name = "site_management/delivery_tracker/form.html"
    fields = [
        "item",
        "supplier",
        "ordered_date",
        "expected_delivery_date",
        "actual_delivery_date",
        "delivered_quantity",
        "remarks",
    ]
    widgets = {
        "ordered_date": DateInput(attrs={"type": "date"}),
        "expected_delivery_date": DateInput(attrs={"type": "date"}),
        "actual_delivery_date": DateInput(attrs={"type": "date"}),
    }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, widget in self.widgets.items():
            form.fields[field_name].widget = widget
        return form

    def form_valid(self, form):
        messages.success(self.request, "Delivery tracker updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:delivery-tracker-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class DeliveryTrackerDeleteView(DeliveryTrackerMixin, DeleteView):
    """Delete a delivery tracker."""

    template_name = "site_management/delivery_tracker/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Delivery tracker deleted successfully!")
        return reverse_lazy(
            "site_management:delivery-tracker-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
