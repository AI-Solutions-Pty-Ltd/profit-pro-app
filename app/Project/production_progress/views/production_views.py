from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, TemplateView
from django.urls import reverse_lazy

from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Account.subscription_config import Subscription
from app.Project.models import Project

from ..models.production_models import DailyProduction, ProductionPlan
from ..forms.production_forms import DailyProductionForm, ProductionPlanForm


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
        return reverse_lazy("project:production-planning", kwargs={"project_pk": self.kwargs["project_pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        context["plans"] = ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])
        return context

    def form_valid(self, form):
        form.instance.project_id = self.kwargs["project_pk"]
        return super().form_valid(form)

class ProductionCostBreakdownView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """Financial analysis view showing the actual cost breakdown vs budget totals."""
    
    template_name = "production_progress/cost_breakdown.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        # Add financial metrics calculation context here
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
        return reverse_lazy("project:production-dashboard", kwargs={"project_pk": self.kwargs["project_pk"]})

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
