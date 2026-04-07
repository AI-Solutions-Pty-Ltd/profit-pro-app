from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.profitability_forms import MaterialCostTrackerForm
from app.Project.models import MaterialCostTracker
from app.Project.profitability.views import ProfitabilityMixin


class MaterialCostTrackerListView(ProfitabilityMixin, ListView):
    model = MaterialCostTracker
    template_name = "profitability/materials/list.html"
    context_object_name = "logs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from decimal import Decimal
        from django.db.models import F, Sum

        # Entity-specific Total Cost
        context["kvi_total_cost"] = (
            self.project.material_cost_logs.aggregate(
                total=Sum(F("quantity") * F("rate"))
            )["total"]
            or 0
        )

        # Entity budget (look for a Category named "Material")
        budget_query = self.project.categories.filter(name__icontains="Material").first()
        context["kvi_budget"] = budget_query.budget if budget_query else Decimal("0.00")
        context["kvi_under_budget"] = context["kvi_budget"] - Decimal(
            context["kvi_total_cost"]
        )

        return context


class MaterialCostTrackerCreateView(ProfitabilityMixin, CreateView):
    model = MaterialCostTracker
    form_class = MaterialCostTrackerForm
    template_name = "profitability/materials/form.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-material-list",
            kwargs={"project_pk": self.project.pk},
        )


class MaterialCostTrackerUpdateView(ProfitabilityMixin, UpdateView):
    model = MaterialCostTracker
    form_class = MaterialCostTrackerForm
    template_name = "profitability/materials/form.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-material-list",
            kwargs={"project_pk": self.project.pk},
        )


class MaterialCostTrackerDeleteView(ProfitabilityMixin, DeleteView):
    model = MaterialCostTracker
    template_name = "profitability/confirm_delete.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-material-list",
            kwargs={"project_pk": self.project.pk},
        )
