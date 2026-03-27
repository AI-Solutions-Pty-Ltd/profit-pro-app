from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    CreateView,
    TemplateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib import messages

from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Account.subscription_config import Subscription
from app.Project.models import Project

from ..models.production_models import (
    DailyProduction,
    ProductionPlan,
    ProductionResource,
    DailyActivityReport,
    DailyActivityEntry,
    DailyLabourUsage,
    DailyPlantUsage,
)
from ..forms.production_forms import (
    DailyProductionForm,
    ProductionPlanForm,
    ProductionResourceForm,
    DailyActivityReportForm,
    DailyActivityEntryForm,
    DailyLabourUsageForm,
    DailyPlantUsageForm,
    DailyLabourUsageFormSet,
    DailyPlantUsageFormSet,
)
from django.shortcuts import redirect, get_object_or_404, render
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, F
from django.forms import inlineformset_factory
from collections import defaultdict


class ProductionDashboardView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """Summarizes daily logs, cumulative progress vs budget."""

    model = DailyProduction
    template_name = "production_progress/dashboard.html"
    context_object_name = "productions"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return DailyProduction.objects.filter(project_id=self.kwargs["project_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])

        # Get filter parameters
        activity_filter = self.request.GET.get("activity", "").strip()
        start_date_filter = self.request.GET.get("start_date", "").strip()
        finish_date_filter = self.request.GET.get("finish_date", "").strip()

        # Build queryset with filters
        plans = ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

        if activity_filter:
            plans = plans.filter(activity__icontains=activity_filter)

        if start_date_filter:
            plans = plans.filter(start_date__gte=start_date_filter)

        if finish_date_filter:
            plans = plans.filter(finish_date__lte=finish_date_filter)

        context["plans"] = plans
        context["activity_filter"] = activity_filter
        context["start_date_filter"] = start_date_filter
        context["finish_date_filter"] = finish_date_filter

        return context


class ProductionPlanningView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Provides a schedule dashboard to plan daily production targets."""

    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = "production_progress/planning.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_success_url(self):
        return reverse_lazy(
            "project:production-dashboard",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        context["plans"] = ProductionPlan.objects.filter(
            project_id=self.kwargs["project_pk"]
        )
        return context

    def form_valid(self, form):
        form.instance.project_id = self.kwargs["project_pk"]
        messages.success(self.request, "Production plan saved successfully.")
        return super().form_valid(form)


class ProductionPlanDetailView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """Shows a single production plan detail."""

    model = ProductionPlan
    template_name = "production_progress/plan_detail.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_object()
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        
        # Prepare structured resource categories for the template
        resource_categories = []
        for type_code, type_name in ProductionResource.RESOURCE_TYPES:
            resources = plan.resources.filter(resource_type=type_code)
            total_cost = 0
            if type_code == 'LABOUR':
                total_cost = plan.total_labour_cost
            elif type_code == 'PLANT':
                total_cost = plan.total_plant_cost
            else:
                total_cost = plan.total_other_cost
                
            resource_categories.append({
                'type_code': type_code,
                'type_name': type_name,
                'resources': resources,
                'total_cost': total_cost
            })
            
        context["resource_categories"] = resource_categories
        return context


class ProductionPlanUpdateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, UpdateView
):
    """Edit an existing production plan item."""

    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = "production_progress/planning.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

    def get_success_url(self):
        return reverse_lazy(
            "project:production-dashboard",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        context["plans"] = ProductionPlan.objects.filter(
            project_id=self.kwargs["project_pk"]
        )
        context["is_update"] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, "Production plan updated successfully.")
        return super().form_valid(form)


class ProductionPlanDeleteView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DeleteView
):
    """Delete an existing production plan item."""

    model = ProductionPlan
    template_name = "production_progress/plan_confirm_delete.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

    def get_success_url(self):
        return reverse_lazy(
            "project:production-dashboard",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Production plan deleted successfully.")
        return super().delete(request, *args, **kwargs)


class ProductionCostBreakdownView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """Financial analysis view showing the actual cost breakdown vs budget totals."""

    template_name = "production_progress/cost_breakdown.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.get(pk=self.kwargs["project_pk"])
        context["project"] = project
        
        # Selection logic: get specific plan if plan_id is provided
        all_plans = ProductionPlan.objects.filter(project=project).order_by('activity')
        plan_id = self.request.GET.get("plan_id")
        
        selected_plan = None
        if plan_id:
            try:
                selected_plan = all_plans.get(pk=plan_id)
            except (ProductionPlan.DoesNotExist, ValueError):
                pass
        
        context["all_plans"] = all_plans
        context["selected_plan"] = selected_plan
        # If a plan is selected, only pass that one to the 'plans' context for display
        context["plans"] = [selected_plan] if selected_plan else []
        
        initial = {}
        if selected_plan:
            initial['production_plan'] = selected_plan
            
        context["resource_form"] = ProductionResourceForm(
            project_id=project.pk,
            initial=initial
        )
        return context

    def post(self, request, *args, **kwargs):
        project_pk = self.kwargs["project_pk"]
        action = request.POST.get("action")

        if action == "delete":
            resource_id = request.POST.get("resource_id")
            try:
                resource = ProductionResource.objects.get(id=resource_id)
                resource_name = resource.name
                resource.delete()
                messages.success(
                    request, f"Resource '{resource_name}' deleted successfully."
                )
            except ProductionResource.DoesNotExist:
                messages.error(request, "Resource not found.")

        return redirect("project:production-cost-breakdown", project_pk=project_pk)


class ProductionResourceCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Form to add a production resource."""

    model = ProductionResource
    form_class = ProductionResourceForm
    template_name = "production_progress/production_resource_form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_success_url(self):
        url = reverse_lazy(
            "project:production-cost-breakdown",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )
        plan_id = self.request.GET.get("plan_id")
        if plan_id:
            return f"{url}?plan_id={plan_id}"
        return url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project_id"] = self.kwargs["project_pk"]
        
        # Determine which fields should be read-only based on query parameters
        disabled_fields = []
        if self.request.GET.get("plan_id") or (self.request.method == "POST" and self.request.POST.get("production_plan")):
            disabled_fields.append("production_plan")
        if self.request.GET.get("type") or (self.request.method == "POST" and self.request.POST.get("resource_type")):
            disabled_fields.append("resource_type")
            
        kwargs["disabled_fields"] = disabled_fields
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        
        # In Django, if a field is disabled, it must be provided in initial
        # so that it holds its value during validation/POST re-rendering.
        plan_id = self.request.GET.get("plan_id") or self.request.POST.get("production_plan")
        resource_type = self.request.GET.get("type") or self.request.POST.get("resource_type")
        
        if plan_id:
            initial["production_plan"] = plan_id
        if resource_type:
            initial["resource_type"] = resource_type
            
        return initial

    def form_valid(self, form):
        resource = form.save()
        messages.success(self.request, f"Resource '{resource.name}' added successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.get(pk=self.kwargs["project_pk"])
        context["project"] = project
        
        # Try to get plan_id from GET and then from POST (e.g. on validation error)
        plan_id = self.request.GET.get("plan_id")
        if not plan_id and self.request.method == "POST":
            plan_id = self.request.POST.get("production_plan")
            
        if plan_id:
            try:
                context["production_plan"] = ProductionPlan.objects.get(pk=plan_id, project=project)
            except (ProductionPlan.DoesNotExist, ValueError):
                pass
                
        return context


class DailyProductionCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Form to log daily quantities."""

    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "production_progress/production_form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_success_url(self):
        return reverse_lazy(
            "project:production-dashboard",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def form_valid(self, form):
        form.instance.project_id = self.kwargs["project_pk"]
        return super().form_valid(form)



class DailyProductivityCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """View to handle the composite Daily Productivity Form (3B)."""
    template_name = "production_progress/productivity_form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        
        plan_id = self.request.GET.get("plan_id")
        selected_plan = None
        if plan_id:
            selected_plan = get_object_or_404(ProductionPlan, pk=plan_id, project=project)

        context["project"] = project
        context["selected_plan"] = selected_plan
        context["report_form"] = kwargs.get("report_form") or DailyActivityReportForm(initial={'date': timezone.now().date()})
        context["entry_form"] = kwargs.get("entry_form") or DailyActivityEntryForm(project_id=project_pk, initial={'production_plan': selected_plan})
        
        # If we have a selected plan, pre-populate resources
        initial_labour = []
        initial_plant = []
        if selected_plan:
            labour_res = ProductionResource.objects.filter(production_plan=selected_plan, resource_type='LABOUR')
            initial_labour = [{'resource': res} for res in labour_res]
            plant_res = ProductionResource.objects.filter(production_plan=selected_plan, resource_type='PLANT')
            initial_plant = [{'resource': res} for res in plant_res]

        if "labour_formset" not in kwargs:
            labour_extra = len(initial_labour) if initial_labour else 3
            LabourFormSet = inlineformset_factory(
                DailyActivityEntry, DailyLabourUsage, form=DailyLabourUsageForm, extra=labour_extra, can_delete=True
            )
            context["labour_formset"] = LabourFormSet(prefix="labour", initial=initial_labour)
            # Ensure the resource field is filtered and set if we have initial data
            for i, form in enumerate(context["labour_formset"]):
                if i < len(initial_labour):
                    form.fields['resource'].queryset = ProductionResource.objects.filter(production_plan=selected_plan, resource_type='LABOUR')
        else:
            context["labour_formset"] = kwargs["labour_formset"]

        if "plant_formset" not in kwargs:
            plant_extra = len(initial_plant) if initial_plant else 3
            PlantFormSet = inlineformset_factory(
                DailyActivityEntry, DailyPlantUsage, form=DailyPlantUsageForm, extra=plant_extra, can_delete=True
            )
            context["plant_formset"] = PlantFormSet(prefix="plant", initial=initial_plant)
            for i, form in enumerate(context["plant_formset"]):
                if i < len(initial_plant):
                    form.fields['resource'].queryset = ProductionResource.objects.filter(production_plan=selected_plan, resource_type='PLANT')
        else:
            context["plant_formset"] = kwargs["plant_formset"]
            
        context["all_plans"] = ProductionPlan.objects.filter(project=project)
        
        return context

    def post(self, request, *args, **kwargs):
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        
        report_form = DailyActivityReportForm(request.POST)
        entry_form = DailyActivityEntryForm(request.POST, project_id=project_pk)
        
        if report_form.is_valid() and entry_form.is_valid():
            with transaction.atomic():
                # 1. Get or create the report for this project and date
                report, created = DailyActivityReport.objects.get_or_create(
                    project=project,
                    date=report_form.cleaned_data["date"]
                )

                # 2. Save the Entry
                entry = entry_form.save(commit=False)
                entry.report = report
                entry.save()

                # 3. Save Formsets
                labour_formset = DailyLabourUsageFormSet(request.POST, instance=entry, prefix="labour")
                plant_formset = DailyPlantUsageFormSet(request.POST, instance=entry, prefix="plant")

                if labour_formset.is_valid() and plant_formset.is_valid():
                    labour_formset.save()
                    plant_formset.save()
                    messages.success(request, "Daily productivity log saved successfully.")
                    return redirect("project:production-dashboard", project_pk=project_pk)
                else:
                    # If formsets are invalid, we need to re-render with errors
                    # This is simplified; in a real app, you'd handle this more gracefully
                    messages.error(request, "Please correct the errors in the resource forms.")
        
        # If any form is invalid, re-render the page
        return self.render_to_response(self.get_context_data(
            report_form=report_form,
            entry_form=entry_form,
            labour_formset=DailyLabourUsageFormSet(request.POST, prefix="labour"),
            plant_formset=DailyPlantUsageFormSet(request.POST, prefix="plant")
        ))


class ProductivityLogsView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """Consolidated view for Labour Log, Plant Log, and Productivity Table."""
    template_name = "production_progress/productivity_logs.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project

        # Get all plans for this project
        plans = ProductionPlan.objects.filter(project=project)
        
        # Get all entries for this project
        entries = DailyActivityEntry.objects.filter(report__project=project).order_by('report__date')
        
        # Organize data for Table 2C (Labour Log) and 2D (Plant Log)
        # We need to map dates to D1, D2 etc. 
        # For simplicity, let's group by plan and then by day.
        
        logs_data = []
        for plan in plans:
            plan_entries = entries.filter(production_plan=plan)
            if not plan_entries.exists():
                continue
                
            labour_resources = ProductionResource.objects.filter(production_plan=plan, resource_type='LABOUR')
            plant_resources = ProductionResource.objects.filter(production_plan=plan, resource_type='PLANT')
            
            day_list = []
            # Get unique day numbers from entries
            day_identifiers = sorted(list(set(entry.day_number for entry in plan_entries)), key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
            
            day_data = {}
            for day_id in day_identifiers:
                # Find the entry that matches the day_id (D1, D2 etc)
                entry = next((e for e in plan_entries if e.day_number == day_id), None)
                if not entry:
                    continue
                
                labour_usage_map = {usage.resource_id: usage.number for usage in entry.labour_usage.all()}
                plant_usage_map = {usage.resource_id: usage.number for usage in entry.plant_usage.all()}
                
                day_data[day_id] = {
                    'entry': entry,
                    'labour_usage': labour_usage_map,
                    'plant_usage': plant_usage_map,
                    'total_labourers': sum(usage.number for usage in entry.labour_usage.all()),
                    'total_labour_cost': entry.total_labour_cost,
                    'avg_hours': sum(usage.hours for usage in entry.labour_usage.all()) / entry.labour_usage.count() if entry.labour_usage.exists() else 0,
                    'man_hours': entry.man_hours,
                    'total_plant_cost': entry.total_plant_cost,
                    'production': entry.quantity,
                    'total_cost': entry.total_cost,
                    'productivity': entry.work_productivity,
                    'cost_per_item': entry.cost_per_item,
                }

            logs_data.append({
                'plan': plan,
                'days_list': day_identifiers,
                'day_data': day_data,
                'labour_resources': labour_resources,
                'plant_resources': plant_resources,
            })

        context["logs_data"] = logs_data
        return context


class ProgressTrackingView(ProductivityLogsView):
    """View to display the data from the analysis view, with daily breakdowns."""
    template_name = "production_progress/progress_tracking.html"
