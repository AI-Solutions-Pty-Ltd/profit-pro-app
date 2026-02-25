"""CRUD views for Procurement Tracker."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import ProcurementTracker


class ProcurementTrackerMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Procurement Tracker views."""

    model = ProcurementTracker
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return ProcurementTracker.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Procurement Tracker", url=None),
        ]


class ProcurementTrackerListView(ProcurementTrackerMixin, ListView):
    """List all procurement trackers."""

    template_name = "site_management/procurement_tracker/list.html"
    context_object_name = "procurement_trackers"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class ProcurementTrackerCreateView(ProcurementTrackerMixin, CreateView):
    """Create a new procurement tracker."""

    template_name = "site_management/procurement_tracker/form.html"
    fields = [
        "item",
        "supplier",
        "ordered_date",
        "invoice_number",
        "quantity",
        "delivery_status",
        "payment_status",
        "remarks",
    ]
    widgets = {"ordered_date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["ordered_date"].widget = self.widgets["ordered_date"]
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Procurement tracker created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:procurement-tracker-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class ProcurementTrackerUpdateView(ProcurementTrackerMixin, UpdateView):
    """Update a procurement tracker."""

    template_name = "site_management/procurement_tracker/form.html"
    fields = [
        "item",
        "supplier",
        "ordered_date",
        "invoice_number",
        "quantity",
        "delivery_status",
        "payment_status",
        "remarks",
    ]
    widgets = {"ordered_date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["ordered_date"].widget = self.widgets["ordered_date"]
        return form

    def form_valid(self, form):
        messages.success(self.request, "Procurement tracker updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:procurement-tracker-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class ProcurementTrackerDeleteView(ProcurementTrackerMixin, DeleteView):
    """Delete a procurement tracker."""

    template_name = "site_management/procurement_tracker/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Procurement tracker deleted successfully!")
        return reverse_lazy(
            "site_management:procurement-tracker-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
