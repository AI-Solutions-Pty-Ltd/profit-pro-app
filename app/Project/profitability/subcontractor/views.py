from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.profitability_forms import SubcontractorCostTrackerForm
from app.Project.models import SubcontractorCostTracker
from app.Project.profitability.views import ProfitabilityMixin


class SubcontractorCostTrackerListView(ProfitabilityMixin, ListView):
    model = SubcontractorCostTracker
    template_name = "profitability/subcontractor/list.html"
    context_object_name = "logs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from decimal import Decimal

        from django.db.models import F, Sum

        # Entity-specific Total Cost
        context["kvi_total_cost"] = (
            self.project.subcontractor_cost_logs.aggregate(
                total=Sum(F("amount_of_days") * F("rate"))
            )["total"]
            or 0
        )

        # Entity budget (look for a Category named "Subcontractor")
        budget_query = self.project.categories.filter(
            name__icontains="Subcontractor"
        ).first()
        context["kvi_budget"] = budget_query.budget if budget_query else Decimal("0.00")
        context["kvi_under_budget"] = context["kvi_budget"] - Decimal(
            context["kvi_total_cost"]
        )

        return context


class SubcontractorCostTrackerCreateView(ProfitabilityMixin, CreateView):
    model = SubcontractorCostTracker
    form_class = SubcontractorCostTrackerForm
    template_name = "profitability/subcontractor/form.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-subcontractor-list",
            kwargs={"project_pk": self.project.pk},
        )


class SubcontractorCostTrackerUpdateView(ProfitabilityMixin, UpdateView):
    model = SubcontractorCostTracker
    form_class = SubcontractorCostTrackerForm
    template_name = "profitability/subcontractor/form.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-subcontractor-list",
            kwargs={"project_pk": self.project.pk},
        )


class SubcontractorCostTrackerDeleteView(ProfitabilityMixin, DeleteView):
    model = SubcontractorCostTracker
    template_name = "profitability/confirm_delete.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-subcontractor-list",
            kwargs={"project_pk": self.project.pk},
        )
