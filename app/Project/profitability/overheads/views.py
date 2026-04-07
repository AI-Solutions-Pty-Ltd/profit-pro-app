from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.profitability_forms import OverheadCostTrackerForm
from app.Project.models import OverheadCostTracker
from app.Project.profitability.views import ProfitabilityMixin


class OverheadCostTrackerListView(ProfitabilityMixin, ListView):
    model = OverheadCostTracker
    template_name = "profitability/overheads/list.html"
    context_object_name = "logs"


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
