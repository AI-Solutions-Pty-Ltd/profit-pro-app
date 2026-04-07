from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from app.Project.profitability.views import ProfitabilityMixin
from .models import PlantCostTracker

class PlantCostTrackerListView(ProfitabilityMixin, ListView):
    model = PlantCostTracker
    template_name = "profitability/plant_equipment/list.html"
    context_object_name = "logs"

class PlantCostTrackerCreateView(ProfitabilityMixin, CreateView):
    model = PlantCostTracker
    template_name = "profitability/form.html"
    fields = ["plant_entity", "date", "usage_hours", "hourly_rate"]

    def get_success_url(self):
        return reverse_lazy("project:profitability-plant-list", kwargs={"project_pk": self.project.pk})

class PlantCostTrackerUpdateView(ProfitabilityMixin, UpdateView):
    model = PlantCostTracker
    template_name = "profitability/form.html"
    fields = ["plant_entity", "date", "usage_hours", "hourly_rate"]

    def get_success_url(self):
        return reverse_lazy("project:profitability-plant-list", kwargs={"project_pk": self.project.pk})

class PlantCostTrackerDeleteView(ProfitabilityMixin, DeleteView):
    model = PlantCostTracker
    template_name = "profitability/confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("project:profitability-plant-list", kwargs={"project_pk": self.project.pk})
