from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from app.Project.models import Project
from app.Project.production_progress.models.production_models import DailyLabourUsage, DailyPlantUsage, ProductionResource

from ..forms import LabourCostLogForm, OverheadCostLogForm, SubcontractorCostLogForm
from ..models.profitability_models import LabourCostLog, OverheadCostLog, SubcontractorCostLog

class ProfitabilityDashboardView(DetailView):
    model = Project
    template_name = "profitability/dashboard.html"
    context_object_name = "project"
    pk_url_kwarg = "project_pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        # 1. Baseline Data (Aggregated from Production Plans)
        planned_resources = ProductionResource.objects.filter(production_plan__project=project)
        total_planned_cost = planned_resources.aggregate(total=Sum('total_cost'))['total'] or 0

        # We'll use a dictionary to mimic the BaselineAssumption model structure
        # Since we don't have a formal Baseline model yet, we'll derive what we can
        baseline = {
            "total_planned_cost": total_planned_cost,
            "planned_revenue": 0,  # Placeholder
            "planned_profit": 0,   # Placeholder
            "target_margin_percentage": 0, # Placeholder
            "planned_labour_cost": 0, # Placeholder
            "planned_material_cost": 0, # Placeholder
            "planned_subcontractor_cost": 0, # Placeholder
            "planned_overhead_cost": 0, # Placeholder
        }

        # 2. Actual Costs from Production Logs
        actual_labour_logs = DailyLabourUsage.objects.filter(entry__report__project=project)
        actual_plant_logs = DailyPlantUsage.objects.filter(entry__report__project=project)

        actual_prod_labour = sum(log.total_cost for log in actual_labour_logs)
        actual_prod_plant = sum(log.total_cost for log in actual_plant_logs)

        # 3. New Profitability Tracker Costs
        sub_costs = SubcontractorCostLog.objects.filter(project=project).aggregate(total=Sum('total_cost'))['total'] or 0
        extra_labour_costs = LabourCostLog.objects.filter(project=project).aggregate(total=Sum('total_cost'))['total'] or 0
        overhead_costs = OverheadCostLog.objects.filter(project=project).aggregate(total=Sum('total_cost'))['total'] or 0

        total_actual_cost = actual_prod_labour + actual_prod_plant + sub_costs + extra_labour_costs + overhead_costs
        variance_val = total_planned_cost - total_actual_cost

        # Structured context for new UI
        context['baseline'] = baseline
        context['actuals'] = {
            "labour": actual_prod_labour + extra_labour_costs,
            "material": 0, # Placeholder
            "subcontractor": sub_costs,
            "overhead": overhead_costs,
            "total_cost": total_actual_cost,
            "plant": actual_prod_plant,
        }
        
        context['variance'] = {
            "total_cost": variance_val,
            "percentage": (variance_val / total_planned_cost * 100) if total_planned_cost > 0 else 0,
        }

        context.update({
            "total_planned_cost": total_planned_cost,
            "total_actual_cost": total_actual_cost,
            "variance_val": variance_val,
            "sub_costs": sub_costs,
            "extra_labour_costs": extra_labour_costs,
            "overhead_costs": overhead_costs,
            "actual_prod_labour": actual_prod_labour,
            "actual_prod_plant": actual_prod_plant,
        })
        return context

# --- Subcontractor Views ---
class SubcontractorListView(ListView):
    model = SubcontractorCostLog
    template_name = "profitability/subcontractor/list.html"
    context_object_name = "logs"

    def get_queryset(self):
        return SubcontractorCostLog.objects.filter(project_id=self.kwargs["project_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        return context

class SubcontractorCreateView(CreateView):
    model = SubcontractorCostLog
    form_class = SubcontractorCostLogForm
    template_name = "profitability/subcontractor/form.html"

    def form_valid(self, form):
        form.instance.project_id = self.kwargs["project_pk"]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("project:profitability-subcontractor-list", kwargs={"project_pk": self.kwargs["project_pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["title"] = "Add Subcontractor Cost"
        return context

# --- Labour Views ---
class LabourListView(ListView):
    model = LabourCostLog
    template_name = "profitability/labour/list.html"
    context_object_name = "logs"
    def get_queryset(self): return LabourCostLog.objects.filter(project_id=self.kwargs["project_pk"])
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        return context

class LabourCreateView(CreateView):
    model = LabourCostLog
    form_class = LabourCostLogForm
    template_name = "profitability/labour/form.html"
    def form_valid(self, form):
        form.instance.project_id = self.kwargs["project_pk"]
        return super().form_valid(form)
    def get_success_url(self): return reverse_lazy("project:profitability-labour-list", kwargs={"project_pk": self.kwargs["project_pk"]})
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["title"] = "Add Labour Cost"
        return context

# --- Overhead Views ---
class OverheadListView(ListView):
    model = OverheadCostLog
    template_name = "profitability/overheads/list.html"
    context_object_name = "logs"
    def get_queryset(self): return OverheadCostLog.objects.filter(project_id=self.kwargs["project_pk"])
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        return context

class OverheadCreateView(CreateView):
    model = OverheadCostLog
    form_class = OverheadCostLogForm
    template_name = "profitability/overheads/form.html"
    def form_valid(self, form):
        form.instance.project_id = self.kwargs["project_pk"]
        return super().form_valid(form)
    def get_success_url(self): return reverse_lazy("project:profitability-overhead-list", kwargs={"project_pk": self.kwargs["project_pk"]})
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["title"] = "Add Overhead Cost"
        return context

# Placeholder for Coming Soon
class ComingSoonView(TemplateView):
    template_name = "profitability/coming_soon.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["feature_name"] = self.kwargs.get("feature_name", "Feature")
        return context
