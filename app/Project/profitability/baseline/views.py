from django.urls import reverse
from django.views.generic import UpdateView
from django.contrib import messages

from app.Project.forms.profitability_forms import ProfitabilityBaselineForm
from app.Project.models import ProfitabilityBaseline
from app.Project.profitability.views import ProfitabilityMixin
from app.Project.profitability.mixins import FinancialCalculationMixin


class ProfitabilityBaselineUpdateView(ProfitabilityMixin, FinancialCalculationMixin, UpdateView):
    """
    View to capture and update baseline assumptions for a project.
    Since it's a OneToOne relationship, we ensure the object exists for the project.
    """

    model = ProfitabilityBaseline
    form_class = ProfitabilityBaselineForm
    template_name = "profitability/baseline/baseline_assumptions.html"

    def get_object(self, queryset=None):
        """Return the baseline for the project, creating it if it doesn't exist."""
        obj, created = ProfitabilityBaseline.objects.get_or_create(project=self.project)
        return obj

    def get_success_url(self):
        messages.success(self.request, "Baseline assumptions updated successfully.")
        return reverse(
            "project:profitability-baseline", kwargs={"project_pk": self.project.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add values for UI richness/comparison if needed
        context["current_baseline"] = self.get_baseline_assumptions()
        return context
