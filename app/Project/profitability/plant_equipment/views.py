from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.profitability.views import ProfitabilityMixin

from .models import PlantCostTracker


class PlantCostTrackerListView(ProfitabilityMixin, ListView):
    model = PlantCostTracker
    template_name = "profitability/plant_equipment/list.html"
    context_object_name = "logs"
    auto_import_type = "plant"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from decimal import Decimal

        from django.db.models import F, Sum

        # Entity-specific Total Cost
        context["kvi_total_cost"] = (
            self.project.plant_cost_logs.aggregate(  # type: ignore
                total=Sum(F("usage_hours") * F("hourly_rate"))
            )["total"]
            or 0
        )

        # Entity budget (look for a Category named "Plant")
        budget_query = self.project.categories.filter(name__icontains="Plant").first()
        context["kvi_budget"] = budget_query.budget if budget_query else Decimal("0.00")
        context["kvi_under_budget"] = context["kvi_budget"] - Decimal(
            context["kvi_total_cost"]
        )

        return context


class PlantCostTrackerCreateView(ProfitabilityMixin, CreateView):
    model = PlantCostTracker
    template_name = "profitability/form.html"
    fields = ["plant_entity", "date", "usage_hours", "hourly_rate"]

    def get_success_url(self):
        return reverse_lazy(
            "project:profitability-plant-list", kwargs={"project_pk": self.project.pk}
        )


class PlantCostTrackerUpdateView(ProfitabilityMixin, UpdateView):
    model = PlantCostTracker
    template_name = "profitability/form.html"
    fields = ["plant_entity", "date", "usage_hours", "hourly_rate"]

    def get_success_url(self):
        return reverse_lazy(
            "project:profitability-plant-list", kwargs={"project_pk": self.project.pk}
        )


class PlantCostTrackerDeleteView(ProfitabilityMixin, DeleteView):
    model = PlantCostTracker
    template_name = "profitability/confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy(
            "project:profitability-plant-list", kwargs={"project_pk": self.project.pk}
        )
