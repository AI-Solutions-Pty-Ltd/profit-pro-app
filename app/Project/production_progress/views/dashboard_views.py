from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project

from ..production_models import (
    DailyProduction,
    ProductionPlan,
)
from ..utils.production_utils import (
    get_activity_detail_data,
    get_dashboard_data,
    get_plan_productivity_data,
)


class ProductionDashboardView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """Summarizes daily logs, cumulative progress vs budget."""

    model = DailyProduction
    template_name = "production_progress/dashboard/dashboard.html"
    context_object_name = "productions"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return DailyProduction.objects.filter(
            project_id=self.kwargs["project_pk"],
        ).select_related("project")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])

        # Get filter parameters
        activity_filter = self.request.GET.get("activity", "").strip()
        start_date_filter = self.request.GET.get("start_date", "").strip()
        finish_date_filter = self.request.GET.get("finish_date", "").strip()

        # Build queryset with filters
        plans = ProductionPlan.objects.filter(
            project_id=self.kwargs["project_pk"], is_archived=False
        ).prefetch_related("resources")

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


class ProductionProgressDashboardView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """
    Electronic Production Progress Dashboard.
    Provides a high-level overview of all production activities.
    """

    template_name = "production_progress/dashboard/production_progress_dashboard.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        # Filters
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        status_filter = self.request.GET.get("status")

        # Get data from utils
        dashboard_data = get_dashboard_data(project_pk, start_date, end_date)

        # Filter item cards by status if requested
        if status_filter:
            dashboard_data["item_cards"] = [
                card
                for card in dashboard_data["item_cards"]
                if card["status_text"] == status_filter
            ]

        context.update(
            {
                "project": project,
                **dashboard_data,
                "start_date": start_date,
                "end_date": end_date,
                "status_filter": status_filter,
            }
        )
        return context


class ProductionActivityDetailView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """
    Detailed Electronic Progress Dashboard for a single activity.
    """

    model = ProductionPlan
    template_name = "production_progress/dashboard/plan_progress_detail.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        # Get detailed metrics from utils
        activity_data = get_activity_detail_data(self.object.pk)

        context.update(
            {
                "project": project,
                **activity_data,
            }
        )
        return context


class PlanProductivityDashboardView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """
    Plan Productivity Dashboard.
    Compares planned production targets against actual performance.
    """

    template_name = "production_progress/dashboard/plan_productivity_dashboard.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        # Filters
        plan_id = self.request.GET.get("plan_id")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        all_plans = ProductionPlan.objects.filter(project=project).order_by("activity")

        # Default to first plan if none selected
        selected_plan = None
        if plan_id:
            selected_plan = all_plans.filter(pk=plan_id).first()
        if not selected_plan and all_plans.exists():
            selected_plan = all_plans.first()

        # Get data from utils
        dashboard_data = get_plan_productivity_data(
            selected_plan.pk if selected_plan else None, start_date, end_date
        )

        context.update(
            {
                "project": project,
                "all_plans": all_plans,
                "selected_plan": selected_plan,
                "start_date": start_date,
                "end_date": end_date,
                **dashboard_data,
            }
        )
        return context
