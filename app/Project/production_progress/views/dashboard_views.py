from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import DetailView, TemplateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project

from ..production_forms import PlanFilterForm
from ..production_models import (
    ProductionPlan,
)
from ..utils.production_utils import (
    get_activity_detail_data,
    get_plan_productivity_data,
)


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

        # Initialize filter form
        plan_filter_form = PlanFilterForm(self.request.GET, project_id=project_pk)

        all_plans = ProductionPlan.objects.filter(
            project=project, labour_activity__isnull=False
        ).order_by("activity")

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
                "plan_filter_form": plan_filter_form,
                **dashboard_data,
            }
        )

        return context

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Project Management",
                "url": reverse_lazy(
                    "project:project-management", kwargs={"pk": project_pk}
                ),
            },
            {"title": "Productivity Forecast", "url": None},
        ]
