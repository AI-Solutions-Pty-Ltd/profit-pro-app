"""CRUD views for Plant Equipment."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import PlantEquipment


class PlantEquipmentMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Plant Equipment views."""

    model = PlantEquipment
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return PlantEquipment.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Plant & Equipment", url=None),
        ]


class PlantEquipmentListView(PlantEquipmentMixin, ListView):
    """List all plant equipment."""

    template_name = "site_management/plant_equipment/list.html"
    context_object_name = "plant_equipment"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class PlantEquipmentCreateView(PlantEquipmentMixin, CreateView):
    """Create a new plant equipment entry."""

    template_name = "site_management/plant_equipment/form.html"
    fields = [
        "date",
        "equipment_name",
        "supplier",
        "usage_hours",
        "breakdown_status",
        "maintenance_done",
        "remarks",
    ]
    widgets = {"date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Plant equipment entry created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:plant-equipment-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class PlantEquipmentUpdateView(PlantEquipmentMixin, UpdateView):
    """Update a plant equipment entry."""

    template_name = "site_management/plant_equipment/form.html"
    fields = [
        "date",
        "equipment_name",
        "supplier",
        "usage_hours",
        "breakdown_status",
        "maintenance_done",
        "remarks",
    ]
    widgets = {"date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        return form

    def form_valid(self, form):
        messages.success(self.request, "Plant equipment entry updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:plant-equipment-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class PlantEquipmentDeleteView(PlantEquipmentMixin, DeleteView):
    """Delete a plant equipment entry."""

    template_name = "site_management/plant_equipment/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Plant equipment entry deleted successfully!")
        return reverse_lazy(
            "site_management:plant-equipment-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
