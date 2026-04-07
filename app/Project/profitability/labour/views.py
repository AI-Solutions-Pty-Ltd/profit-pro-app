from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.profitability_forms import LabourCostTrackerForm
from app.Project.models import LabourCostTracker
from app.Project.profitability.views import ProfitabilityMixin


class LabourCostTrackerListView(ProfitabilityMixin, ListView):
    model = LabourCostTracker
    template_name = "profitability/labour/list.html"
    context_object_name = "logs"


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
