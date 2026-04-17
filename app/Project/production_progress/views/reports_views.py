import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project
from app.core.Utilities.widgets import SearchableSelectWidget

from ..production_models import (
    DailyActivityEntry,
    ProductionPlan,
    ProductionResource,
)
from ..utils.production_utils import (
    get_forecasting_dashboard_data,
)


class ProductivityLogsView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """Consolidated view for Labour Log, Plant Log, and Productivity Table."""

    template_name = "production_progress/tracking/productivity_logs.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": "Productivity Logs", "url": None},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project

        # Get all plans for this project - only work activities (with labour spec)
        plans = ProductionPlan.objects.filter(
            project=project, labour_activity__isnull=False
        )

        # Get all entries for this project
        entries = DailyActivityEntry.objects.filter(report__project=project).order_by(
            "report__date"
        )

        logs_data = []
        for plan in plans:
            plan_entries = entries.filter(production_plan=plan).prefetch_related(
                "labour_usage",
                "plant_usage",
                "labour_usage__resource",
                "plant_usage__resource",
            )
            if not plan_entries.exists():
                continue

            labour_resources = ProductionResource.objects.filter(
                production_plan=plan, resource_type="LABOUR"
            )
            plant_resources = ProductionResource.objects.filter(
                production_plan=plan, resource_type="PLANT"
            )

            # Get unique day numbers from entries
            day_identifiers = sorted(
                {entry.day_number for entry in plan_entries},
                key=lambda x: int(x[1:]) if x[1:].isdigit() else 0,
            )

            day_data = {}
            for day_id in day_identifiers:
                entry = next((e for e in plan_entries if e.day_number == day_id), None)
                if not entry:
                    continue

                labour_usage_map = {
                    usage.resource.id: usage.number
                    for usage in entry.labour_usage.all()
                }
                plant_usage_map = {
                    usage.resource.id: usage.number for usage in entry.plant_usage.all()
                }

                day_data[day_id] = {
                    "entry": entry,
                    "labour_usage": labour_usage_map,
                    "plant_usage": plant_usage_map,
                    "total_labourers": sum(
                        usage.number for usage in entry.labour_usage.all()
                    ),
                    "total_labour_cost": entry.total_labour_cost,
                    "avg_hours": sum(usage.hours for usage in entry.labour_usage.all())
                    / entry.labour_usage.count()
                    if entry.labour_usage.exists()
                    else 0,
                    "man_hours": entry.man_hours,
                    "total_plant_cost": entry.total_plant_cost,
                    "production": entry.quantity,
                    "total_cost": entry.total_cost,
                    "productivity": entry.work_productivity,
                    "cost_per_item": entry.cost_per_item,
                }

            logs_data.append(
                {
                    "plan": plan,
                    "days_list": day_identifiers,
                    "day_data": day_data,
                    "labour_resources": labour_resources,
                    "plant_resources": plant_resources,
                }
            )

        context["logs_data"] = logs_data
        return context


class ProductionForecastDashboardView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """
    Costing Forecasting Dashboard.
    Provides predictive analytics on project completion timelines and budget outcomes.
    """

    template_name = "production_progress/reports/forecast_dashboard.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": "Forecasting Dashboard", "url": None},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        # Filters
        plan_id = self.request.GET.get("plan_id")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        all_plans = ProductionPlan.objects.filter(
            project=project, labour_activity__isnull=False
        ).order_by("activity")

        selected_plan = None
        if plan_id:
            try:
                selected_plan = all_plans.filter(pk=plan_id).first()
            except (ValueError, TypeError):
                pass
        if not selected_plan and all_plans.exists():
            selected_plan = all_plans.first()

        forecast_data = {}
        if selected_plan:
            forecast_data = get_forecasting_dashboard_data(
                selected_plan.pk, start_date, end_date
            )

        charts_json = "{}"
        if "charts" in forecast_data:
            charts_json = json.dumps(forecast_data["charts"])

        # Prepare Searchable Select Widget
        plan_choices = []
        for p in all_plans:
            label = p.activity
            hierarchy = []
            if p.section:
                hierarchy.append(p.section)
            if p.bill_no:
                hierarchy.append(p.bill_no)
            if hierarchy:
                label = f"{label} ({' / '.join(hierarchy)})"
            plan_choices.append((p.pk, label))

        plan_widget = SearchableSelectWidget(choices=plan_choices)
        plan_selector_widget = plan_widget.render(
            "plan_id",
            selected_plan.pk if selected_plan else None,
            attrs={"id": "plan_id", "onchange": "this.form.submit()"},
        )

        context.update(
            {
                "project": project,
                "all_plans": all_plans,
                "selected_plan": selected_plan,
                "start_date": start_date,
                "end_date": end_date,
                "plan_selector_widget": plan_selector_widget,
                **forecast_data,
                "charts_json": charts_json,
            }
        )
        return context
