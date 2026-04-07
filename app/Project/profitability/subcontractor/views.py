from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.profitability_forms import SubcontractorCostTrackerForm
from app.Project.models import SubcontractorCostTracker
from app.Project.profitability.views import ProfitabilityMixin


class SubcontractorCostTrackerListView(ProfitabilityMixin, ListView):
    model = SubcontractorCostTracker
    template_name = "profitability/subcontractor/list.html"
    context_object_name = "logs"


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
    template_name = "profitability/subcontractor/confirm_delete.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-subcontractor-list",
            kwargs={"project_pk": self.project.pk},
        )
