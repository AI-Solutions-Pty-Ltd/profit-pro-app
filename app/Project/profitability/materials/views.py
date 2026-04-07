from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.profitability_forms import MaterialCostTrackerForm
from app.Project.models import MaterialCostTracker
from app.Project.profitability.views import ProfitabilityMixin


class MaterialCostTrackerListView(ProfitabilityMixin, ListView):
    model = MaterialCostTracker
    template_name = "profitability/materials/list.html"
    context_object_name = "logs"


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
