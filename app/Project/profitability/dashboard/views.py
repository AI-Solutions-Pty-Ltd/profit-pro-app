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

        context["total_project_expenditure"] = (
            context["total_journal_amount"]
            + context["total_subcontractor_cost"]
            + context["total_labour_cost"]
            + context["total_overhead_cost"]
        )

        return context
