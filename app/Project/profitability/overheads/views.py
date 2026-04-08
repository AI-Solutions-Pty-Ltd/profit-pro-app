from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.profitability_forms import OverheadCostTrackerForm
from app.Project.models import OverheadCostTracker
from app.Project.profitability.views import ProfitabilityMixin


class OverheadCostTrackerListView(ProfitabilityMixin, ListView):
    model = OverheadCostTracker
    template_name = "profitability/overheads/list.html"
    context_object_name = "logs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from decimal import Decimal

        from django.db.models import F, Sum

        # Entity-specific Total Cost
        context["kvi_total_cost"] = (
            self.project.overhead_cost_logs.aggregate(  # type: ignore
                total=Sum(F("amount_of_days") * F("rate"))
            )["total"]
            or 0
        )

        # Entity budget (look for a Category named "Overhead")
        budget_query = self.project.categories.filter(
            name__icontains="Overhead"
        ).first()
        context["kvi_budget"] = budget_query.budget if budget_query else Decimal("0.00")
        context["kvi_under_budget"] = context["kvi_budget"] - Decimal(
            context["kvi_total_cost"]
        )

        return context


class OverheadCostTrackerCreateView(ProfitabilityMixin, CreateView):
    model = OverheadCostTracker
    form_class = OverheadCostTrackerForm
    template_name = "profitability/overheads/form.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-overhead-list",
            kwargs={"project_pk": self.project.pk},
        )


class OverheadCostTrackerUpdateView(ProfitabilityMixin, UpdateView):
    model = OverheadCostTracker
    form_class = OverheadCostTrackerForm
    template_name = "profitability/overheads/form.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-overhead-list",
            kwargs={"project_pk": self.project.pk},
        )


class OverheadCostTrackerDeleteView(ProfitabilityMixin, DeleteView):
    model = OverheadCostTracker
    template_name = "profitability/confirm_delete.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-overhead-list",
            kwargs={"project_pk": self.project.pk},
        )
