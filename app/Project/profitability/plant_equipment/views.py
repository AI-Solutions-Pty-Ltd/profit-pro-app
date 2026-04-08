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

        from django.db.models import Avg, F, Max, Min, Sum

        # Current monthly queryset (already filtered by self.get_queryset via ProfitabilityMixin)
        logs_qs = self.get_queryset()

        # 1. Total Monthly Cost
        context["kvi_total_cost"] = (
            logs_qs.aggregate(total=Sum(F("usage_hours") * F("hourly_rate")))["total"]
            or 0
        )

        # 2. Total Monthly Hours
        context["kvi_metric_name"] = "Total Usage Hours"
        context["kvi_metric_value"] = (
            logs_qs.aggregate(total=Sum("usage_hours"))["total"] or 0
        )

        # 3. Rate Statistics (Average, High, Low)
        rate_stats = logs_qs.aggregate(
            avg=Avg("hourly_rate"), max=Max("hourly_rate"), min=Min("hourly_rate")
        )
        context["kvi_avg_rate"] = rate_stats["avg"] or 0
        context["kvi_max_rate"] = rate_stats["max"] or 0
        context["kvi_min_rate"] = rate_stats["min"] or 0
        context["kvi_rate_label"] = "Hourly Rate"

        # Entity budget (look for a Category named "Plant")
        budget_query = self.project.categories.filter(name__icontains="Plant").first()
        context["kvi_budget"] = budget_query.budget if budget_query else Decimal("0.00")
        context["kvi_under_budget"] = context["kvi_budget"] - Decimal(
            str(context["kvi_total_cost"])
        )

        return context


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from decimal import Decimal

        from django.db.models import F, Sum

        # Entity-specific Total Cost
        context["kvi_total_cost"] = (
            self.project.plant_cost_logs.aggregate(
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
