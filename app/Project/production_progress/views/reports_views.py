import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.core.Utilities.widgets import SearchableSelectWidget
from app.Project.models import Project

from ..production_models import (
    DailyActivityEntry,
    ProductionPlan,
    ProductionResource,
)
from ..utils.production_utils import (
    get_forecasting_dashboard_data,
    get_premium_productivity_report_data,
    get_project_performance_summary,
    get_project_productivity_report_data,
)


class ProductionProductivityReportView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """
    Premium Productivity Report View.
    Replicates Excel logic for PPI/CPI and impact analysis.
    """

    template_name = "production_progress/reports/productivity_report.html"
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
            {"title": "Productivity Report", "url": None},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        # Filters
        horizon = self.request.GET.get("horizon", "ptd")
        active_only = self.request.GET.get("active_only") == "true"

        # Fetch premium report data
        data = get_premium_productivity_report_data(
            project_pk, horizon=horizon, active_only=active_only
        )

        context.update(
            {
                "project": project,
                "company": project.contractor,
                "summary": data.get("summary", {}),
                "sections": data.get("sections", []),
                "active_horizon": horizon,
                "active_only": active_only,
                "tab": "productivity_report",
            }
        )
        return context


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
            plan_choices.append((p.pk, p.activity))

        plan_widget = SearchableSelectWidget(choices=plan_choices)
        plan_selector_widget = plan_widget.render(
            "plan_id",
            selected_plan.pk if selected_plan else None,
            attrs={"id": "plan_id", "onchange": "this.form.submit()"},
        )

        context.update(
            {
                "project": project,
                "company": project.contractor,
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


class ProductionPerformanceReportView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """
    Comprehensive Project Performance Report.
    Focuses on Project-wide Productivity Index (PPI), Cost Performance Index (CPI),
    and multi-horizon accumulation forecasts.
    """

    template_name = "production_progress/reports/performance_report.html"
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
            {"title": "Performance Analytics", "url": None},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        # Extract horizons from GET parameters
        history_horizon = self.request.GET.get("history", "3m")
        forecast_horizon = self.request.GET.get("forecast", "3m")

        # Fetch comprehensive report data
        data = get_project_productivity_report_data(
            project_pk, history_horizon, forecast_horizon
        )

        # JSON serialize charts for Chart.js
        charts_json = json.dumps(data.get("charts", {}))

        context.update(
            {
                "project": project,
                "company": project.contractor,
                "summary": data.get("summary", {}),
                "charts": data.get("charts", {}),
                "forecasts": data.get("forecasts", {}),
                "activities": data.get("activities", []),
                "charts_json": charts_json,
                "active_history": history_horizon,
                "active_forecast": forecast_horizon,
            }
        )
        return context


class ProductionProgressReportView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """
    Production Progress Report View.
    Filtered to show only activities with actual progress.
    Includes a Progress Gantt Chart and a detailed metrics table.
    """

    template_name = "production_progress/reports/progress_report.html"
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
            {"title": "Progress Report", "url": None},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        today = timezone.now().date()

        # Fetch basic performance data (PPI etc)
        perf_data = get_project_performance_summary(project_pk)
        ppi = perf_data.get("ppi", Decimal("1.0"))

        # Get all plans with progress > 0
        all_plans = ProductionPlan.objects.filter(
            project=project, is_archived=False, is_leaf=True
        ).prefetch_related("daily_entries", "predecessors")

        report_items = []

        for plan in all_plans:
            progress_pct = plan.progress_percentage
            if progress_pct <= 0:
                continue

            total_produced = (
                plan.daily_entries.aggregate(total=Sum("quantity"))["total"] or 0
            )
            remaining_qty = max(0, plan.quantity - total_produced)

            # Forecasting
            forecast_end_date = plan.finish_date
            if remaining_qty > 0:
                current_rate = plan.daily_rate * ppi
                if current_rate > 0:
                    days_left = int(remaining_qty / current_rate)
                    forecast_end_date = today + timedelta(days=days_left)

            days_variance = 0
            if plan.finish_date and forecast_end_date:
                days_variance = (forecast_end_date - plan.finish_date).days

            # Schedule Variance (Simplified for this view: Estimated vs Planned Duration)
            spi = ppi  # Using PPI as SPI proxy for now

            item = {
                "plan": plan,
                "planned_duration": plan.duration,
                "forecast_end_date": forecast_end_date,
                "days_variance": days_variance,
                "progress_pct": progress_pct,
                "spi": float(spi),
                "schedule_variance": days_variance * -1,
            }
            report_items.append(item)

        context.update(
            {
                "project": project,
                "company": project.contractor,
                "report_items": report_items,
                "summary": perf_data,
                "tab": "production_progress_report",
            }
        )
        return context


class ProductionControllerView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """
    Integrated Production Control Center.
    Combines the Gantt Schedule and Progress Metrics Table into a single synchronized view.
    """

    template_name = "production_progress/reports/integrated_control.html"
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
            {"title": "Integrated Control Center", "url": None},
        ]

    @staticmethod
    def _flatten_tree(plans, parent_id=None, depth=0):
        """Reused from Gantt view to build ordered list."""
        rows = []
        for plan in plans:
            if plan.parent_id == parent_id:
                rows.append((plan, depth))
                rows.extend(
                    ProductionControllerView._flatten_tree(plans, plan.pk, depth + 1)
                )
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        today = timezone.now().date()

        # 1. Fetch Performance Summary (PPI etc)
        perf_data = get_project_performance_summary(project_pk)
        ppi = perf_data.get("ppi", Decimal("1.0"))
        context.update(
            {
                "project": project,
                "summary": perf_data,
                "tab": "integrated_control",
            }
        )

        # 2. Gantt Data Logic (Reused from ProductionPlanGanttView)
        all_plans = list(
            ProductionPlan.objects.filter(
                project=project,
                is_archived=False,
                start_date__isnull=False,
                finish_date__isnull=False,
            )
            .select_related("labour_activity", "parent")
            .prefetch_related(
                "predecessors",
                "predecessors__predecessor",
                "children",
                "daily_entries",
            )
            .order_by("section", "bill_no", "start_date")
        )
        context["plans"] = all_plans
        ordered = self._flatten_tree(all_plans)

        # 2. Progress Data (Unified KPI Logic for Gantt & Table)
        from app.Project.production_progress.utils.production_utils import (
            get_plan_forecast_kpis,
        )

        gantt_data = []
        report_items = []

        # Aggregates for KPI Cards & Project Health
        planned_dates = []
        forecast_dates = []
        total_p_qty = Decimal("0")
        total_a_qty = Decimal("0")

        # Map to store KPIs for aggregation
        plan_kpis = {}

        # First pass: Calculate leaf node KPIs and collect project totals
        for plan, depth in ordered:
            if plan.is_leaf:
                kpis = get_plan_forecast_kpis(plan, ppi)
                plan_kpis[plan.id] = kpis

                total_p_qty += plan.quantity
                total_a_qty += Decimal(str(kpis["summary"]["completed_units"]))

                if plan.finish_date:
                    planned_dates.append(plan.finish_date)
                if kpis["daily_output"]["forecast_finish"]:
                    forecast_dates.append(kpis["daily_output"]["forecast_finish"])

        # Second pass: Build report items with parent aggregation
        for plan, depth in ordered:
            kpis = plan_kpis.get(plan.id)

            if not plan.is_leaf:
                # Aggregate for headers (Section/Bill)
                # Find all leaf descendants in the 'ordered' list

                def get_descendants(p_id):
                    res = []
                    for p, _d in ordered:
                        if p.parent_id == p_id:
                            if p.is_leaf:
                                res.append(p)
                            else:
                                res.extend(get_descendants(p.id))
                    return res

                # Optimized: Since we have plan_kpis for leaves, just find those
                leaf_children = get_descendants(plan.id)
                child_kpis = [
                    plan_kpis[lc.id] for lc in leaf_children if lc.id in plan_kpis
                ]

                if child_kpis:
                    # Aggregate Forecast Finish
                    f_finish = max(
                        [
                            k["daily_output"]["forecast_finish"]
                            for k in child_kpis
                            if k["daily_output"]["forecast_finish"]
                        ]
                    )

                    # Aggregate Progress (Weighted)
                    c_planned = sum([lc.quantity for lc in leaf_children])
                    c_actual = sum(
                        [
                            Decimal(str(k["summary"]["completed_units"]))
                            for k in child_kpis
                        ]
                    )
                    c_prog = float(c_actual / c_planned * 100) if c_planned > 0 else 0

                    # Estimate Parent SPI (Weighted)
                    # We'll use the same project PPI logic or weighted average
                    c_spi = (
                        float(
                            sum(
                                [
                                    k["daily_output"]["index"] * float(lc.quantity)
                                    for k, lc in zip(child_kpis, leaf_children, strict=False)
                                ]
                            )
                        )
                        / float(c_planned)
                        if c_planned > 0
                        else float(ppi)
                    )

                    # Mock a KPI object for the parent
                    kpis = {
                        "daily_output": {
                            "forecast_finish": f_finish,
                            "index": c_spi,
                            "time_variance": (plan.finish_date - f_finish).days
                            if plan.finish_date and f_finish
                            else 0,
                            "days_remaining": sum(
                                [
                                    k["daily_output"]["days_remaining"]
                                    for k in child_kpis
                                ]
                            ),
                            "forecast_duration": (f_finish - plan.start_date).days
                            if plan.start_date and f_finish
                            else 0,
                        },
                        "summary": {
                            "progress_pct": round(c_prog, 1),
                            "completed_units": float(c_actual),
                            "remaining_units": float(c_planned - c_actual),
                            "status": "Ongoing",
                            "status_color": "indigo",
                        },
                    }

            # Prepare Gantt JSON Data
            prog = kpis["summary"]["progress_pct"] if kpis else 0
            f_fin = (
                kpis["daily_output"]["forecast_finish"] if kpis else plan.finish_date
            )

            gantt_data.append(
                {
                    "id": str(plan.id),
                    "activity": plan.activity,
                    "start_date": plan.start_date.isoformat(),
                    "finish_date": plan.finish_date.isoformat(),
                    "forecast_finish_date": f_fin.isoformat() if f_fin else None,
                    "progress_pct": float(prog),
                    "parent_id": str(plan.parent_id) if plan.parent_id else None,
                    "has_children": plan.children.exists(),
                    "depth": depth,
                    "predecessors": [
                        str(dep.predecessor_id) for dep in plan.predecessors.all()
                    ],
                }
            )

            # Add to table if it's a leaf or has children with data
            if kpis:
                report_items.append(
                    {
                        "plan": plan,
                        "depth": depth,
                        "kpis": kpis,
                        "progress_pct": kpis["summary"]["progress_pct"],
                        "status": kpis["summary"]["status"],
                        "status_color": kpis["summary"]["status_color"],
                        "spi": kpis["daily_output"]["index"],
                    }
                )

        context["gantt_data_json"] = json.dumps(gantt_data)

        # 3. Finalize Project-Level Metrics for KPI Cards
        # Ensure we match the "Production Plan" scope (all_plans)
        project_planned_finish = max(planned_dates) if planned_dates else None
        project_forecast_finish = max(forecast_dates) if forecast_dates else None

        overrun_days = 0
        if project_planned_finish and project_forecast_finish:
            overrun_days = (project_forecast_finish - project_planned_finish).days

        # Overall Progress calculated from the same plan quantities
        overall_prog = float(total_a_qty / total_p_qty * 100) if total_p_qty > 0 else 0

        context["project_kpis"] = {
            "planned_finish": project_planned_finish,
            "forecast_finish": project_forecast_finish,
            "overrun_days": overrun_days,
            "progress_pct": round(overall_prog, 1),
            "spi": float(ppi),
        }

        context["report_items"] = report_items
        return context
