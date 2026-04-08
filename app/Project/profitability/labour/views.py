from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.profitability_forms import LabourCostTrackerForm
from app.Project.models import LabourCostTracker
from app.Project.profitability.views import ProfitabilityMixin


class LabourCostTrackerListView(ProfitabilityMixin, ListView):
    model = LabourCostTracker
    template_name = "profitability/labour/list.html"
    context_object_name = "logs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from decimal import Decimal

        from django.db.models import F, Sum

        # Entity-specific Total Cost
        context["kvi_total_cost"] = (
            self.project.labour_cost_logs.aggregate(
                total=Sum(F("amount_of_days") * F("salary"))
            )["total"]
            or 0
        )

        # Entity budget (look for a Category named "Labour")
        budget_query = self.project.categories.filter(name__icontains="Labour").first()
        context["kvi_budget"] = budget_query.budget if budget_query else Decimal("0.00")
        context["kvi_under_budget"] = context["kvi_budget"] - Decimal(
            context["kvi_total_cost"]
        )

        return context


class LabourCostTrackerCreateView(ProfitabilityMixin, CreateView):
    model = LabourCostTracker
    form_class = LabourCostTrackerForm
    template_name = "profitability/labour/form.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-labour-list", kwargs={"project_pk": self.project.pk}
        )


class LabourCostTrackerUpdateView(ProfitabilityMixin, UpdateView):
    model = LabourCostTracker
    form_class = LabourCostTrackerForm
    template_name = "profitability/labour/form.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-labour-list", kwargs={"project_pk": self.project.pk}
        )


class LabourCostTrackerDeleteView(ProfitabilityMixin, DeleteView):
    model = LabourCostTracker
    template_name = "profitability/confirm_delete.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-labour-list", kwargs={"project_pk": self.project.pk}
        )
