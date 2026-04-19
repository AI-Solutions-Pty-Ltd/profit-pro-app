from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..production_models import DailyActivityEntry, ProductionPlan


def calculate_progress_status(produced, planned, start_date=None, finish_date=None):
    """
    Determines status based on progress vs target and schedule.
    Returns (status_text, color_class)
    """
    if not planned or planned == 0:
        return "Not Planned", "gray"

    progress_pct = (Decimal(produced) / Decimal(planned)) * 100

    # Ensure we have dates for schedule-based status
    if not start_date or not finish_date:
        if progress_pct > 0:
            return "In Progress", "yellow"
        return "Not Started", "gray"

    # Check if behind schedule
    is_behind = False
    if timezone.now().date() > finish_date and progress_pct < 100:
        is_behind = True

    if progress_pct >= 90 and not is_behind:
        return "On Track", "green"
    elif progress_pct >= 30 and not is_behind:
        return "In Progress", "yellow"
    else:
        return "Delayed", "red"


def calculate_trend(current_umh, previous_umh):
    """
    Calculates percentage change between two productivity values.
    Returns (percentage_change, is_positive)
    """
    if not previous_umh or previous_umh == 0:
        return 0, True

    change = (
        (Decimal(current_umh) - Decimal(previous_umh)) / Decimal(previous_umh)
    ) * 100
    return round(change, 1), change >= 0


def get_dashboard_data(project_id, start_date=None, end_date=None):
    """
    Aggregates all project data for the dashboard with optimized queries.
    """
    plans = ProductionPlan.objects.filter(
        project_id=project_id, labour_activity__isnull=False
    )
    entries_qs = (
        DailyActivityEntry.objects.filter(report__project_id=project_id)
        .select_related("report")
        .prefetch_related(
            "labour_usage",
            "plant_usage",
            "labour_usage__resource",
            "plant_usage__resource",
        )
    )

    if start_date:
        entries_qs = entries_qs.filter(report__date__gte=start_date)
    if end_date:
        entries_qs = entries_qs.filter(report__date__lte=end_date)

    all_entries = list(entries_qs)

    # Group entries by plan_id
    entries_by_plan = defaultdict(list)
    for entry in all_entries:
        entries_by_plan[entry.production_plan_id].append(entry)

    # 2. Overall Metrics
    total_planned = plans.aggregate(total=Sum("quantity"))["total"] or 0
    total_produced = sum(entry.quantity for entry in all_entries)

    total_spent = Decimal("0.0")
    total_hours = Decimal("0.0")

    for entry in all_entries:
        total_spent += entry.total_cost
        total_hours += entry.man_hours

    worker_days = round(total_hours / 8, 1)
    active_items_count = plans.count()

    overall_progress_pct = 0
    if total_planned > 0:
        overall_progress_pct = round((total_produced / total_planned) * 100, 1)

    # 3. Item-Specific Data
    item_cards = []
    status_counts = {"On_Track": 0, "In_Progress": 0, "Delayed": 0, "Not_Planned": 0}

    for plan in plans:
        plan_entries = sorted(entries_by_plan[plan.id], key=lambda x: x.report.date)
        plan_produced = sum(entry.quantity for entry in plan_entries)

        plan_spent = sum(entry.total_cost for entry in plan_entries)
        plan_hours = sum(entry.man_hours for entry in plan_entries)

        umh = 0
        if plan_hours > 0:
            umh = round(plan_produced / plan_hours, 1)

        # Trend Calculation
        trend_val = 0
        trend_positive = True
        if len(plan_entries) >= 2:
            last_entry = plan_entries[-1]
            # Previous productivity: Total produced / Total hours for all entries BEFORE the last one
            prev_entries = plan_entries[:-1]
            p_produced = sum(e.quantity for e in prev_entries)
            p_hours = sum(e.man_hours for e in prev_entries)

            current_umh = last_entry.work_productivity
            prev_umh = 0
            if p_hours > 0:
                prev_umh = p_produced / p_hours

            trend_val, trend_positive = calculate_trend(current_umh, prev_umh)

        day_indicator = "N/A"
        if plan_entries:
            day_indicator = plan_entries[-1].day_number

        comp_pct = 0
        if plan.quantity > 0:
            comp_pct = int((plan_produced / plan.quantity) * 100)

        status_text, status_color = calculate_progress_status(
            plan_produced, plan.quantity, plan.start_date, plan.finish_date
        )

        status_key = status_text.replace(" ", "_")
        status_counts[status_key] = status_counts.get(status_key, 0) + 1

        remaining_qty = max(0, plan.quantity - plan_produced)

        # Convert spent to 'k' for display if large
        display_spent = (
            round(plan_spent / 1000, 1) if plan_spent >= 1000 else plan_spent
        )

        item_cards.append(
            {
                "plan": plan,
                "status_text": status_text,
                "status_color": status_color,
                "day_indicator": day_indicator,
                "completion_pct": min(100, comp_pct),
                "produced_qty": plan_produced,
                "remaining_qty": remaining_qty,
                "spent": display_spent,
                "hours": plan_hours,
                "umh": umh,
                "trend_val": trend_val,
                "trend_positive": trend_positive,
            }
        )

    return {
        "total_produced": total_produced,
        "total_planned": total_planned,
        "total_spent": total_spent,
        "total_hours": total_hours,
        "worker_days": worker_days,
        "active_items_count": active_items_count,
        "overall_progress_pct": min(100, overall_progress_pct),
        "status_counts": status_counts,
        "item_cards": item_cards,
    }


def get_activity_detail_data(plan_id):
    """
    Fetches detailed metrics for a single production plan item.
    """
    plan = get_object_or_404(ProductionPlan, pk=plan_id)
    entries = (
        DailyActivityEntry.objects.filter(production_plan=plan)
        .select_related("report")
        .prefetch_related(
            "labour_usage",
            "plant_usage",
            "labour_usage__resource",
            "plant_usage__resource",
        )
        .order_by("report__date")
    )

    total_produced = sum(entry.quantity for entry in entries)
    total_spent = sum(entry.total_cost for entry in entries)
    total_hours = sum(entry.man_hours for entry in entries)
    worker_days = round(total_hours / 8, 1) if total_hours > 0 else 0

    avg_productivity = 0
    if total_hours > 0:
        avg_productivity = round(total_produced / total_hours, 2)

    cost_per_item = 0
    if total_produced > 0:
        cost_per_item = round(total_spent / total_produced, 2)

    # Trend Calculation
    trend_val = 0
    trend_positive = True
    if len(entries) >= 2:
        last_entry = list(entries)[-1]
        prev_entries = list(entries)[:-1]
        p_produced = sum(e.quantity for e in prev_entries)
        p_hours = sum(e.man_hours for e in prev_entries)

        current_umh = last_entry.work_productivity
        prev_umh = 0
        if p_hours > 0:
            prev_umh = p_produced / p_hours

        trend_val, trend_positive = calculate_trend(current_umh, prev_umh)

    completion_pct = 0
    if plan.quantity > 0:
        completion_pct = round((total_produced / plan.quantity) * 100, 1)

    # Status
    status_text, status_color = calculate_progress_status(
        total_produced, plan.quantity, plan.start_date, plan.finish_date
    )

    # Days Active
    days_active = 0
    if entries.exists():
        first_date = entries[0].report.date
        last_date = list(entries)[-1].report.date
        days_active = (last_date - first_date).days + 1

    # Daily Breakdown
    daily_breakdown = []
    entry_list = list(entries)
    for i, entry in enumerate(entry_list):
        daily_breakdown.append(
            {
                "day_label": entry.day_number,
                "date": entry.report.date,
                "quantity": entry.quantity,
                "cost": entry.total_cost,
                "hours": entry.man_hours,
                "workers": sum(usage.number for usage in entry.labour_usage.all()),
                "productivity": round(entry.work_productivity, 1),
                "note": entry.report.notes or "",
                "is_latest": (i == len(entry_list) - 1),
            }
        )

    return {
        "plan": plan,
        "total_produced": total_produced,
        "total_planned": plan.quantity,
        "completion_pct": min(100, float(completion_pct)),
        "total_spent": total_spent,
        "total_hours": total_hours,
        "worker_days": worker_days,
        "avg_productivity": avg_productivity,
        "cost_per_item": cost_per_item,
        "trend_val": trend_val,
        "trend_positive": trend_positive,
        "status_text": status_text,
        "status_color": status_color,
        "days_active": days_active,
        "daily_breakdown": daily_breakdown,
        "remaining_qty": max(0, plan.quantity - total_produced),
    }


def get_plan_productivity_data(plan_id, start_date=None, end_date=None):
    """
    Calculates detailed productivity metrics (Actual vs Planned) for a specific plan.
    Used for the Plan Productivity Dashboard.
    """
    if not plan_id:
        return {}

    plan = get_object_or_404(ProductionPlan, pk=plan_id)

    # Hierarchical aggregation
    all_plans = [plan]
    if not plan.labour_activity:
        if not plan.bill_no:
            all_plans = ProductionPlan.objects.filter(
                project=plan.project, section=plan.section, deleted=False
            )
        else:
            all_plans = ProductionPlan.objects.filter(
                project=plan.project,
                section=plan.section,
                bill_no=plan.bill_no,
                deleted=False,
            )

    entries_qs = (
        DailyActivityEntry.objects.filter(production_plan__in=all_plans)
        .select_related("report")
        .prefetch_related(
            "labour_usage",
            "plant_usage",
            "labour_usage__resource",
            "plant_usage__resource",
        )
        .order_by("report__date")
    )

    if start_date:
        entries_qs = entries_qs.filter(report__date__gte=start_date)
    if end_date:
        entries_qs = entries_qs.filter(report__date__lte=end_date)

    entries = list(entries_qs)

    # 1. Planned Metrics (Targets)
    planned_man_hours = Decimal("0.0")
    planned_cost = Decimal("0.0")
    total_planned_qty = plan.quantity
    if not plan.labour_activity:
        total_planned_qty = sum(p.quantity for p in all_plans if p.labour_activity)

    for p in all_plans:
        if (
            p.labour_activity
        ):  # Only sum leaf nodes for targets to avoid double counting
            for res in p.resources.filter(resource_type="LABOUR"):
                planned_man_hours += (res.number or 0) * (res.days or 0) * 8
            planned_cost += (
                p.total_labour_cost + p.total_plant_cost + p.total_other_cost
            )

    target_productivity = Decimal("0.0")
    if planned_man_hours > 0:
        target_productivity = Decimal(total_planned_qty) / planned_man_hours

    target_cost_per_item = Decimal("0.0")
    if total_planned_qty > 0:
        target_cost_per_item = planned_cost / Decimal(total_planned_qty)

    target_daily_output = Decimal("0.0")
    if plan.duration > 0:
        target_daily_output = Decimal(total_planned_qty) / Decimal(plan.duration)

    # 2. Actual Metrics
    actual_total_qty = sum(e.quantity for e in entries)
    actual_total_spent = sum(e.total_cost for e in entries)
    actual_total_hours = sum(e.man_hours for e in entries)

    actual_avg_productivity = Decimal("0.0")
    if actual_total_hours > 0:
        actual_avg_productivity = actual_total_qty / actual_total_hours

    actual_avg_cost_per_item = Decimal("0.0")
    if actual_total_qty > 0:
        actual_avg_cost_per_item = actual_total_spent / actual_total_qty

    days_elapsed = len(entries)
    actual_avg_daily_output = Decimal("0.0")
    if days_elapsed > 0:
        actual_avg_daily_output = actual_total_qty / Decimal(days_elapsed)

    # 3. Trends and Variances
    def calc_var(actual, target):
        if not target or target == 0:
            return 0
        return round(((actual - target) / target) * 100, 1)

    # Productivity Trend (Compare latest day vs previous days average)
    prod_trend_val = 0
    prod_trend_pos = True
    if len(entries) >= 2:
        latest = entries[-1].work_productivity
        prev_sum_qty = sum(e.quantity for e in entries[:-1])
        prev_sum_hours = sum(e.man_hours for e in entries[:-1])
        prev_avg = prev_sum_qty / prev_sum_hours if prev_sum_hours > 0 else 0
        prod_trend_val, prod_trend_pos = calculate_trend(latest, prev_avg)

    # Cost Trend
    cost_trend_val = 0
    cost_trend_pos = (
        False  # For cost, positive change is usually "bad", but let's stick to the math
    )
    if len(entries) >= 2:
        latest_cost = entries[-1].cost_per_item
        prev_sum_cost = sum(e.total_cost for e in entries[:-1])
        prev_sum_qty = sum(e.quantity for e in entries[:-1])
        prev_avg_cost = prev_sum_cost / prev_sum_qty if prev_sum_qty > 0 else 0
        cost_trend_val, cost_trend_pos = calculate_trend(latest_cost, prev_avg_cost)

    # Output Trend
    output_trend_val = 0
    output_trend_pos = True
    if len(entries) >= 2:
        latest_out = entries[-1].quantity
        prev_avg_out = sum(e.quantity for e in entries[:-1]) / (len(entries) - 1)
        output_trend_val, output_trend_pos = calculate_trend(latest_out, prev_avg_out)

    # 4. Chart Data Preparation
    labels = [e.day_number for e in entries]
    dates = [e.report.date.strftime("%b %d") for e in entries]

    actual_production = [float(e.quantity) for e in entries]
    target_production = [float(target_daily_output) for _ in entries]

    cum_actual = []
    running_actual = 0
    for q in actual_production:
        running_actual += q
        cum_actual.append(running_actual)

    cum_target = []
    running_target = 0
    for _ in range(len(entries)):
        running_target += float(target_daily_output)
        cum_target.append(running_target)

    productivity_trend = [float(e.work_productivity) for e in entries]
    cost_trend = [float(e.cost_per_item) for e in entries]

    # 5. Daily Summary Breakdown
    daily_summaries = []
    for i, e in enumerate(entries):
        prev_e = entries[i - 1] if i > 0 else None

        # Prod trend arrow
        p_trend_arrow = "up"
        if prev_e and e.work_productivity < prev_e.work_productivity:
            p_trend_arrow = "down"

        # Variance Calculations for UI Bars (Capped at 50% for display)
        prod_var_pct = 0
        if target_daily_output > 0:
            prod_var_pct = float((e.quantity / target_daily_output - 1) * 100)

        cost_var_pct = 0
        if target_cost_per_item > 0:
            cost_var_pct = float((e.cost_per_item / target_cost_per_item - 1) * 100)

        productivity_var_pct = 0
        if target_productivity > 0:
            productivity_var_pct = float(
                (e.work_productivity / target_productivity - 1) * 100
            )

        daily_summaries.append(
            {
                "day": e.day_number,
                "date": e.report.date.strftime("%Y-%m-%d"),
                "actual_qty": float(e.quantity),
                "target_qty": float(target_daily_output),
                "progress_pct": min(
                    100, round(float(e.quantity / target_daily_output) * 100, 1)
                )
                if target_daily_output > 0
                else 0,
                "productivity": float(e.work_productivity),
                "productivity_arrow": p_trend_arrow,
                "cost_per_item": float(e.cost_per_item),
                "total_cost": float(e.total_cost),
                "man_hours": float(e.man_hours),
                "prod_var": round(prod_var_pct, 1),
                "cost_var": round(cost_var_pct, 1),
                "prod_mh_var": round(productivity_var_pct, 1),
                "prod_var_display": min(50, abs(prod_var_pct)),
                "prod_var_pos": prod_var_pct >= 0,
                "cost_var_display": min(50, abs(cost_var_pct)),
                "cost_var_pos": cost_var_pct >= 0,
                "prod_mh_var_display": min(50, abs(productivity_var_pct)),
                "prod_mh_var_pos": productivity_var_pct >= 0,
                "is_cost_over": e.cost_per_item > target_cost_per_item,
                "status": "On Track" if e.quantity >= target_daily_output else "Behind",
            }
        )

    return {
        "kpis": {
            "productivity": {
                "actual": actual_avg_productivity,
                "target": target_productivity,
                "variance": calc_var(actual_avg_productivity, target_productivity),
                "trend": prod_trend_val,
                "trend_pos": prod_trend_pos,
            },
            "cost": {
                "actual": actual_avg_cost_per_item,
                "target": target_cost_per_item,
                "variance": calc_var(actual_avg_cost_per_item, target_cost_per_item),
                "trend": cost_trend_val,
                "trend_pos": not cost_trend_pos,  # Inverse: for cost, down is good
            },
            "man_hours": {
                "actual": actual_total_hours,
                "planned": planned_man_hours,
                "variance": calc_var(actual_total_hours, planned_man_hours),
            },
            "daily_output": {
                "actual": actual_avg_daily_output,
                "target": target_daily_output,
                "variance": calc_var(actual_avg_daily_output, target_daily_output),
                "trend": output_trend_val,
                "trend_pos": output_trend_pos,
            },
        },
        "charts": {
            "labels": labels,
            "dates": dates,
            "actual_production": actual_production,
            "target_production": target_production,
            "cum_actual": cum_actual,
            "cum_target": cum_target,
            "productivity_trend": productivity_trend,
            "target_productivity": float(target_productivity),
            "cost_trend": cost_trend,
            "target_cost": float(target_cost_per_item),
        },
        "daily_summaries": daily_summaries,
    }


def get_forecasting_dashboard_data(plan_id, start_date=None, end_date=None):
    """
    Calculates predictive forecasting metrics and scenarios for a specific plan.
    """
    if not plan_id:
        return {}

    plan = get_object_or_404(ProductionPlan, pk=plan_id)

    # Hierarchical aggregation
    all_plans = [plan]
    if not plan.labour_activity:
        if not plan.bill_no:
            all_plans = ProductionPlan.objects.filter(
                project=plan.project, section=plan.section, deleted=False
            )
        else:
            all_plans = ProductionPlan.objects.filter(
                project=plan.project,
                section=plan.section,
                bill_no=plan.bill_no,
                deleted=False,
            )

    entries_qs = (
        DailyActivityEntry.objects.filter(production_plan__in=all_plans)
        .select_related("report")
        .prefetch_related(
            "labour_usage",
            "plant_usage",
            "labour_usage__resource",
            "plant_usage__resource",
        )
        .order_by("report__date")
    )

    if start_date:
        entries_qs = entries_qs.filter(report__date__gte=start_date)
    if end_date:
        entries_qs = entries_qs.filter(report__date__lte=end_date)

    entries = list(entries_qs)
    days_elapsed = len(entries)

    # 1. Base Metrics (Actual vs Target)
    productive_data = get_plan_productivity_data(plan_id, start_date, end_date)
    kpis = productive_data.get("kpis", {})

    # Extract needed values from KPIs
    actual_avg_out = kpis.get("daily_output", {}).get("actual", Decimal("0.0"))
    target_avg_out = kpis.get("daily_output", {}).get("target", Decimal("0.0"))
    actual_avg_cost = kpis.get("cost", {}).get("actual", Decimal("0.0"))
    target_avg_cost = kpis.get("cost", {}).get("target", Decimal("0.0"))
    actual_total_qty = sum(e.quantity for e in entries)
    actual_total_cost = sum(e.total_cost for e in entries)

    total_planned_qty = plan.quantity
    if not plan.labour_activity:
        total_planned_qty = sum(p.quantity for p in all_plans if p.labour_activity)

    remaining_qty = max(0, float(total_planned_qty) - float(actual_total_qty))

    # Planned budget for all plans in scope
    budget_allocation = Decimal("0.0")
    for p in all_plans:
        if p.labour_activity:
            budget_allocation += (
                p.total_labour_cost + p.total_plant_cost + p.total_other_cost
            )
    progress_pct = (
        (
            float(actual_total_qty) / float(total_planned_qty) * 100
            if total_planned_qty > 0
            else 0
        )
        if plan.quantity > 0
        else 0
    )

    # 2. Forecasting Calculations
    # Time Forecast
    days_to_complete = 0
    if actual_avg_out > 0:
        days_to_complete = float(Decimal(remaining_qty) / Decimal(actual_avg_out))
    else:
        # Fallback to target if no actual data yet
        if target_avg_out > 0:
            days_to_complete = float(Decimal(remaining_qty) / Decimal(target_avg_out))
        else:
            days_to_complete = 0

    forecast_total_days = days_elapsed + days_to_complete
    time_variance = float(plan.duration) - forecast_total_days

    # Cost Forecast
    forecast_remaining_cost = Decimal(remaining_qty) * Decimal(actual_avg_cost)
    forecast_total_at_completion = Decimal(actual_total_cost) + forecast_remaining_cost
    budget_variance = Decimal(budget_allocation) - forecast_total_at_completion

    # 5. Trajectory Data (for composed charts)
    max_days = int(max(plan.duration, forecast_total_days)) + 2
    chart_labels = [f"D{i}" for i in range(1, max_days + 1)]

    actual_prod_traj = []
    actual_cost_traj = []
    curr_prod = 0
    curr_cost = 0
    for e in entries:
        curr_prod += float(e.quantity)
        curr_cost += float(e.total_cost)
        actual_prod_traj.append(curr_prod)
        actual_cost_traj.append(curr_cost)

    planned_prod_traj = []
    planned_cost_traj = []
    daily_target_qty = float(target_avg_out)
    daily_target_cost = float(target_avg_cost * target_avg_out)

    for i in range(1, max_days + 1):
        p_qty = min(float(plan.quantity), i * daily_target_qty)
        p_cost = min(float(budget_allocation), i * daily_target_cost)
        planned_prod_traj.append(round(p_qty, 2))
        planned_cost_traj.append(round(p_cost, 2))

    forecast_prod_traj = [None] * (days_elapsed - 1) + [
        actual_prod_traj[-1] if actual_prod_traj else 0
    ]
    forecast_cost_traj = [None] * (days_elapsed - 1) + [
        actual_cost_traj[-1] if actual_cost_traj else 0
    ]

    for i in range(days_elapsed + 1, max_days + 1):
        f_qty = min(
            float(plan.quantity),
            (actual_prod_traj[-1] if actual_prod_traj else 0)
            + (i - days_elapsed) * float(actual_avg_out),
        )
        f_cost = (actual_cost_traj[-1] if actual_cost_traj else 0) + (
            i - days_elapsed
        ) * float(actual_avg_out) * float(actual_avg_cost)
        forecast_prod_traj.append(round(f_qty, 2))
        forecast_cost_traj.append(round(f_cost, 2))

    return {
        "project": plan.project,
        "selected_plan": plan,
        "kpis": kpis,
        "summary": {
            "status": "Critical"
            if (time_variance < -2 or budget_variance < -50000)
            else (
                "At Risk" if (time_variance < 0 or budget_variance < 0) else "On Track"
            ),
            "status_color": "red"
            if (time_variance < -2 or budget_variance < -50000)
            else ("amber" if (time_variance < 0 or budget_variance < 0) else "emerald"),
            "progress_pct": round(progress_pct, 1),
            "forecast_days": round(forecast_total_days, 1),
            "time_variance": round(time_variance, 1),
            "planned_days": int(plan.duration),
            "forecast_cost": float(forecast_total_at_completion),
            "budget_variance": float(budget_variance),
            "budget_allocation": float(budget_allocation),
            "days_remaining": round(days_to_complete, 1),
            "units_remaining": float(remaining_qty),
            "budget_used_pct": round(
                (float(actual_total_cost) / float(budget_allocation) * 100), 1
            )
            if budget_allocation > 0
            else 0,
        },
        "charts": {
            "labels": chart_labels,
            "actual_prod": actual_prod_traj,
            "planned_prod": planned_prod_traj,
            "forecast_prod": forecast_prod_traj,
            "actual_cost": actual_cost_traj,
            "planned_cost": planned_cost_traj,
            "forecast_cost": forecast_cost_traj,
            "forecast_start_index": days_elapsed - 1,
            "target_qty": float(total_planned_qty),
            "target_budget": float(budget_allocation),
            "daily_variance": productive_data.get("daily_summaries", []),
        },
    }


def get_project_cashflow_data(project_id, horizon_type="month", history_months=3):
    """
    Calculates project-wide cashflow trajectories: Planned, Actual, and Forecast.
    history_months: number of months back from today to start the graph (0 for project start).
    """
    from datetime import timedelta

    from dateutil.relativedelta import relativedelta

    from app.Project.models import Project

    project = get_object_or_404(Project, pk=project_id)
    plans = ProductionPlan.objects.filter(project_id=project_id, is_archived=False)
    entries = DailyActivityEntry.objects.filter(
        report__project_id=project_id
    ).select_related("report")

    today = timezone.now().date()

    # Determine timeframe - only consider plans WITH dates for timeline calculations
    scheduled_plans = plans.filter(start_date__isnull=False, finish_date__isnull=False)

    if not scheduled_plans.exists():
        return {"labels": [], "planned": [], "actual": [], "forecast": [], "kpis": {}}

    # Project inception matches the earliest scheduled plan start
    project_start = min(p.start_date for p in scheduled_plans)
    schedule_finish = max(p.finish_date for p in scheduled_plans)

    # End date based on horizon
    if horizon_type == "term":
        end_date = today + relativedelta(months=3)
    elif horizon_type == "half":
        end_date = today + relativedelta(months=6)
    elif horizon_type == "year":
        end_date = today + relativedelta(years=1)
    else:  # month
        end_date = today + relativedelta(months=1)

    # Display end date
    viz_end_date = max(end_date, schedule_finish)

    # Display start date (history window)
    if history_months and history_months > 0:
        display_start = today - relativedelta(months=history_months)
        # Ensure we don't start before project start if we want to show inception
        # display_start = max(display_start, project_start)
        # Actually, let it start exactly at history_months even if before project start (for consistent width)
        # but capping at project_start is usually cleaner for S-Curves.
        # However, a fixed 3m window is what the user asked for.
    else:
        display_start = project_start

    # Initialize trajectories
    daily_planned = defaultdict(Decimal)
    daily_actual = defaultdict(Decimal)

    # 1. Map Planned Costs (Only for scheduled plans)
    for plan in scheduled_plans:
        total_p_cost = (
            plan.total_labour_cost + plan.total_plant_cost + plan.total_other_cost
        )
        days = (plan.finish_date - plan.start_date).days + 1
        daily_p_cost = total_p_cost / Decimal(days) if days > 0 else total_p_cost

        curr = plan.start_date
        while curr <= plan.finish_date:
            daily_planned[curr] += daily_p_cost
            curr += timedelta(days=1)

    # 2. Map Actual Costs
    for entry in entries:
        daily_actual[entry.report.date] += entry.total_cost

    # 3. Build Monthly Data series
    labels = []
    # Incremental (Monthly)
    planned_inc = []
    actual_inc = []
    # Cumulative (S-Curve)
    planned_cum = []
    actual_cum = []
    forecast_cum = []

    cum_planned = Decimal("0.0")
    cum_actual = Decimal("0.0")
    cum_forecast = Decimal("0.0")

    # Iterate from project START to ensure cumulative totals are accurate
    curr = project_start
    current_month_p = Decimal("0.0")
    current_month_a = Decimal("0.0")

    # Loop day by day to calculate cumulative values
    while curr <= viz_end_date:
        p_val = daily_planned.get(curr, Decimal("0.0"))
        a_val = daily_actual.get(curr, Decimal("0.0"))

        cum_planned += p_val
        if curr <= today:
            cum_actual += a_val
            cum_forecast = cum_actual
            current_month_a += a_val
        else:
            cum_forecast += p_val

        current_month_p += p_val

        # At the end of the month or at the vized_end_date, snapshot the data
        is_month_end = (curr + timedelta(days=1)).month != curr.month
        is_viz_end = curr == viz_end_date

        if is_month_end or is_viz_end:
            # Only record if within display window (OR if it's the very first month of display_start)
            if curr >= display_start.replace(day=1):
                labels.append(curr.strftime("%b %Y"))

                # Monthly Spend (Bars)
                planned_inc.append(float(current_month_p))
                if curr <= today or (
                    curr.month == today.month and curr.year == today.year
                ):
                    actual_inc.append(float(current_month_a))
                else:
                    actual_inc.append(0.0)  # No actuals for future months

                # Cumulative To Date (Lines)
                planned_cum.append(float(cum_planned))
                if curr <= today:
                    actual_cum.append(float(cum_actual))
                    forecast_cum.append(float(cum_forecast))
                else:
                    actual_cum.append(None)
                    forecast_cum.append(float(cum_forecast))

            # Reset monthly counters
            current_month_p = Decimal("0.0")
            current_month_a = Decimal("0.0")

        curr += timedelta(days=1)

    # 4. Calculate KPIs (remains the same)
    month_start = today.replace(day=1)

    # Current Month Actual so far
    month_actual = sum(
        daily_actual.get(d, Decimal("0.0"))
        for d in [
            month_start + timedelta(days=i)
            for i in range((today - month_start).days + 1)
        ]
    )

    # Current Month Planned total
    month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
    month_planned = sum(
        daily_planned.get(month_start + timedelta(days=i), Decimal("0.0"))
        for i in range((month_end - month_start).days + 1)
    )

    f_end = today + relativedelta(months=1)
    if horizon_type == "term":
        f_end = today + relativedelta(months=3)
    elif horizon_type == "half":
        f_end = today + relativedelta(months=6)
    elif horizon_type == "year":
        f_end = today + relativedelta(years=1)

    f_start = today + timedelta(days=1)
    period_forecast = (
        sum(
            daily_planned.get(f_start + timedelta(days=i), Decimal("0.0"))
            for i in range((f_end - f_start).days + 1)
        )
        if f_end >= f_start
        else 0
    )

    monthly_variance = float(month_actual - month_planned)
    is_healthy = monthly_variance <= 0

    return {
        "labels": labels,
        "planned_cum": planned_cum,
        "actual_cum": actual_cum,
        "forecast_cum": forecast_cum,
        "planned_inc": planned_inc,
        "actual_inc": actual_inc,
        "kpis": {
            "month_actual": float(month_actual),
            "month_planned": float(month_planned),
            "monthly_variance": float(monthly_variance),
            "is_healthy": is_healthy,
            "period_forecast": float(period_forecast),
            "total_budget": float(cum_planned),
            "today": today.strftime("%Y-%m-%d"),
            "horizon_label": horizon_type.capitalize(),
        },
    }
