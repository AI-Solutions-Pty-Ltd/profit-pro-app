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
)
from ..forms.production_forms import (
    DailyProductionForm,
    ProductionPlanForm,
    ProductionResourceForm,
)
from django.shortcuts import redirect


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
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
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


class DailyProductionListView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """Historical logs listing."""

    model = DailyProduction
    template_name = "production_progress/production_list.html"
    context_object_name = "productions"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return DailyProduction.objects.filter(project_id=self.kwargs["project_pk"])
