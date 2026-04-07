from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from app.Project.models import Project


class ProfitabilityDashboardView(LoginRequiredMixin, DetailView):
    """
    Main dashboard for Project Profitability Management.
    """

    model = Project
    template_name = "profitability/dashboard.html"
    context_object_name = "project"

    def get_object(self, queryset=None):
        return get_object_or_404(Project, pk=self.kwargs.get("project_pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        # Summary Metrics
        from django.db.models import F, Sum

        context["total_journal_amount"] = (
            project.journal_entries.aggregate(total=Sum("amount"))["total"] or 0
        )
        context["total_subcontractor_cost"] = (
            project.subcontractor_cost_logs.aggregate(
                total=Sum(F("amount_of_days") * F("rate"))
            )["total"]
            or 0
        )
        context["total_labour_cost"] = (
            project.labour_cost_logs.aggregate(
                total=Sum(F("amount_of_days") * F("salary"))
            )["total"]
            or 0
        )
        context["total_overhead_cost"] = (
            project.overhead_cost_logs.aggregate(
                total=Sum(F("amount_of_days") * F("rate"))
            )["total"]
            or 0
        )
        material_logs_cost = (
            project.material_cost_logs.aggregate(
                total=Sum(F("quantity") * F("rate"))
            )["total"]
            or 0
        )
        plant_logs_cost = (
            project.plant_cost_logs.aggregate(
                total=Sum(F("usage_hours") * F("hourly_rate"))
            )["total"]
            or 0
        )
        context["total_material_cost"] = material_logs_cost + plant_logs_cost

        context["total_project_expenditure"] = (
            context["total_journal_amount"]
            + context["total_subcontractor_cost"]
            + context["total_labour_cost"]
            + context["total_overhead_cost"]
            + context["total_material_cost"]
        )

        # Baseline structuring (Mocked for now)
        # In a real scenario, these would come from the BaselineAssumption model
        # We'll use the total actual cost as a base for mock revenue to keep the UI sensible
        from decimal import Decimal
        
        if context["total_project_expenditure"] > 0:
            planned_total = context["total_project_expenditure"] * Decimal("1.1")
        else:
            planned_total = Decimal("100000.00")
        
        context['baseline'] = {
            'planned_revenue': planned_total * Decimal("1.25"),
            'planned_labour_cost': planned_total * Decimal("0.4"),
            'planned_material_cost': planned_total * Decimal("0.3"),
            'planned_subcontractor_cost': planned_total * Decimal("0.2"),
            'planned_overhead_cost': planned_total * Decimal("0.1"),
            'target_margin_percentage': 20.0,
            'total_planned_cost': planned_total,
            'planned_profit': planned_total * Decimal("0.25"),
        }

        # Actuals structuring
        total_actual_cost = context["total_project_expenditure"]
        context['actuals'] = {
            'labour': context["total_labour_cost"],
            'material': context["total_material_cost"],
            'subcontractor': context["total_subcontractor_cost"],
            'overhead': context["total_overhead_cost"],
            'total_cost': total_actual_cost,
        }

        # Variance Analysis
        context['variance'] = {
            'labour': context['baseline']['planned_labour_cost'] - context['actuals']['labour'],
            'material': context['baseline']['planned_material_cost'] - context['actuals']['material'],
            'subcontractor': context['baseline']['planned_subcontractor_cost'] - context['actuals']['subcontractor'],
            'overhead': context['baseline']['planned_overhead_cost'] - context['actuals']['overhead'],
            'total_cost': context['baseline']['total_planned_cost'] - total_actual_cost,
        }
        
        context['actual_profit'] = context['baseline']['planned_revenue'] - total_actual_cost
        if context['baseline']['planned_revenue'] > 0:
            context['actual_margin'] = (context['actual_profit'] / context['baseline']['planned_revenue']) * 100
        else:
            context['actual_margin'] = 0

        return context
