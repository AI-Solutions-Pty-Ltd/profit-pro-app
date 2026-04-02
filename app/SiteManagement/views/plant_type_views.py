"""CRUD views for Plant Types."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.SiteManagement.models import PlantType

from .plant_equipment_views import PlantEquipmentMixin


class PlantTypeListView(PlantEquipmentMixin, ListView):
    """List all plant types for a project."""

    model = PlantType
    template_name = "site_management/plant_type/list.html"
    context_object_name = "plant_types"
    paginate_by = 20

    def get_queryset(self):
        return PlantType.objects.filter(project=self.get_project())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class PlantTypeCreateView(PlantEquipmentMixin, CreateView):
    """Create a new plant type."""

    model = PlantType
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


class PlantTypeUpdateView(PlantEquipmentMixin, UpdateView):
    """Update an existing plant type."""

    model = PlantType
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


class PlantTypeDeleteView(PlantEquipmentMixin, DeleteView):
    """Delete a plant type."""

    model = PlantType
    template_name = "site_management/plant_type/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Plant Type deleted successfully!")
        return reverse_lazy(
            "site_management:plant-type-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
