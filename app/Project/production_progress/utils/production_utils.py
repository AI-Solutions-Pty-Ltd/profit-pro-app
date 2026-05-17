import math
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import (
    Case,
    Count,
    DecimalField,
    F,
    IntegerField,
    Max,
    OuterRef,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Ceil, Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone

from app.Estimator.models import BOQItem, ProjectPlantSpecificationComponent

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
    entries_qs = DailyActivityEntry.objects.filter(
        project_id=project_id
    ).prefetch_related(
        "labour_usage",
        "plant_usage",
        "labour_usage__resource",
        "plant_usage__resource",
    )

    if start_date:
        entries_qs = entries_qs.filter(date__gte=start_date)
    if end_date:
        entries_qs = entries_qs.filter(date__lte=end_date)

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
        plan_entries = sorted(entries_by_plan[plan.id], key=lambda x: x.date)
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
        .prefetch_related(
            "labour_usage",
            "plant_usage",
            "labour_usage__resource",
            "plant_usage__resource",
        )
        .order_by("date")
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
        first_date = entries[0].date
        last_date = list(entries)[-1].date
        days_active = (last_date - first_date).days + 1

    # Daily Breakdown
    daily_breakdown = []
    entry_list = list(entries)
    for i, entry in enumerate(entry_list):
        daily_breakdown.append(
            {
                "day_label": entry.day_number,
                "date": entry.date,
                "quantity": entry.quantity,
                "cost": entry.total_cost,
                "hours": entry.man_hours,
                "workers": sum(usage.number for usage in entry.labour_usage.all()),
                "productivity": round(entry.work_productivity, 1),
                "note": entry.notes or "",
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
        .prefetch_related(
            "labour_usage",
            "plant_usage",
            "labour_usage__resource",
            "plant_usage__resource",
        )
        .order_by("date")
    )

    if start_date:
        entries_qs = entries_qs.filter(date__gte=start_date)
    if end_date:
        entries_qs = entries_qs.filter(date__lte=end_date)

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

    def calc_index(actual, target):
        if not target or target == 0:
            return 1.0
        return round(actual / target, 2)

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
    dates = [e.date.strftime("%b %d") for e in entries]

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
                "date": e.date.strftime("%Y-%m-%d"),
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
                "index": calc_index(actual_avg_productivity, target_productivity),
                "trend": prod_trend_val,
                "trend_pos": prod_trend_pos,
            },
            "cost": {
                "actual": actual_avg_cost_per_item,
                "target": target_cost_per_item,
                "variance": calc_var(actual_avg_cost_per_item, target_cost_per_item),
                "index": calc_index(
                    target_cost_per_item, actual_avg_cost_per_item
                ),  # Cost index: Target / Actual
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
                "index": calc_index(actual_avg_daily_output, target_daily_output),
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


def get_plan_forecast_kpis(plan, project_ppi=1.0):
    """
    Unified calculation for plan forecasting KPIs.
    Returns a dictionary structure compatible with dashboard and table views.
    """
    from datetime import date, timedelta

    from django.db.models import Sum

    # 1. Base Metrics
    actual_total_qty = plan.daily_entries.aggregate(total=Sum("quantity"))["total"] or 0
    entries_count = plan.daily_entries.count()
    today = date.today()

    # 2. Daily Rate & Productivity (Aligned with Dashboard target_daily_output)
    target_rate = 0
    if plan.duration > 0:
        target_rate = float(plan.quantity) / float(plan.duration)
    else:
        target_rate = float(plan.daily_rate)

    # Logic Parity: If plan has data, use its own average output.
    # If not, use project-wide PPI as a forecast proxy.
    actual_avg_out = 0
    ppi = project_ppi

    if entries_count > 0:
        actual_avg_out = float(actual_total_qty) / float(entries_count)
        if target_rate > 0:
            ppi = actual_avg_out / target_rate
    else:
        # Fallback to project performance for new items
        actual_avg_out = target_rate * float(project_ppi)
        ppi = project_ppi

    # 3. Time Forecast
    remaining_qty = max(0, float(plan.quantity) - float(actual_total_qty))
    days_to_complete = 0

    # Use actual average if available, otherwise target
    forecast_rate = actual_avg_out if actual_avg_out > 0 else target_rate

    if forecast_rate > 0:
        days_to_complete = float(remaining_qty) / float(forecast_rate)

    # Brainstorming Refinement: Round up (ceil) days to complete for finish date and duration display
    days_to_complete_rounded = math.ceil(days_to_complete)
    forecast_finish = today + timedelta(days=days_to_complete_rounded)

    # 4. Variance Calculations
    planned_duration = float(plan.duration)
    # Total predicted duration = days already worked + raw days remaining (for accurate variance)
    forecast_total_days_raw = float(entries_count) + float(days_to_complete)
    # Visual Duration = days worked + rounded days remaining (for user display parity)
    forecast_total_days_visual = float(entries_count) + float(days_to_complete_rounded)

    time_variance = planned_duration - forecast_total_days_raw

    # Status Determination
    status = "On Track"
    status_color = "emerald"
    if time_variance < -2:
        status = "Critical"
        status_color = "red"
    elif time_variance < 0:
        status = "At Risk"
        status_color = "amber"

    return {
        "daily_output": {
            "actual": round(actual_avg_out, 1),
            "target": round(target_rate, 1),
            "index": round(ppi, 2),
            "variance": round((float(ppi) - 1) * 100, 1),
            "days_remaining": int(days_to_complete_rounded),  # Rounded up
            "forecast_duration": int(
                forecast_total_days_visual
            ),  # Rounded up (e.g., 5.4 -> 6)
            "forecast_finish": forecast_finish,
            "time_variance": round(time_variance, 1),  # Kept raw (e.g., +2.4d)
            "late_str": f"{'late by' if time_variance < 0 else 'ahead by'} {abs(time_variance):.1f} days",
        },
        "summary": {
            "completed_units": float(actual_total_qty),
            "remaining_units": float(remaining_qty),
            "progress_pct": round(
                (float(actual_total_qty) / float(plan.quantity) * 100), 1
            )
            if plan.quantity > 0
            else 0,
            "status": status,
            "status_color": status_color,
        },
    }


def get_forecasting_dashboard_data(
    plan_id, start_date=None, end_date=None, ppi_override=None
):
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
        .prefetch_related(
            "labour_usage",
            "plant_usage",
            "labour_usage__resource",
            "plant_usage__resource",
        )
        .order_by("date")
    )

    if start_date:
        entries_qs = entries_qs.filter(date__gte=start_date)
    if end_date:
        entries_qs = entries_qs.filter(date__lte=end_date)

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
            "completed_units": float(actual_total_qty),
            "forecast_days": int(days_elapsed + math.ceil(days_to_complete)),
            "time_variance": round(time_variance, 1),
            "planned_days": int(plan.duration),
            "forecast_cost": float(forecast_total_at_completion),
            "budget_variance": float(budget_variance),
            "budget_allocation": float(budget_allocation),
            "days_remaining": int(math.ceil(days_to_complete)),
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
    Calculates project-wide cashflow trajectories: Planned Income, Planned Expenses,
    Actual Expenses, and Forecasted trajectory using project burn rate.
    """
    from datetime import timedelta

    from dateutil.relativedelta import relativedelta
    from django.db.models import Sum

    from app.Project.models import Project

    get_object_or_404(Project, pk=project_id)
    plans = ProductionPlan.objects.filter(project_id=project_id, is_archived=False)
    entries = DailyActivityEntry.objects.filter(project_id=project_id)

    today = timezone.now().date()

    # Determine timeframe - only consider plans WITH dates for timeline calculations
    scheduled_plans = plans.filter(start_date__isnull=False, finish_date__isnull=False)

    if not scheduled_plans.exists():
        return {
            "labels": [],
            "planned_income": [],
            "cost_planned": [],
            "cost_actual": [],
            "cum_cost_planned": [],
            "cum_cost_actual": [],
            "cost_forecast_start_index": 0,
            "kpis": {},
        }

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
    else:
        display_start = project_start

    # Initialize trajectories
    daily_planned_cost = defaultdict(Decimal)
    daily_planned_income = defaultdict(Decimal)
    daily_actual_cost = defaultdict(Decimal)

    # 1. Map Planned Costs & Income (Only for scheduled plans)
    for plan in scheduled_plans:
        # Cost calculation
        total_p_cost = (
            plan.total_labour_cost + plan.total_plant_cost + plan.total_other_cost
        )

        # Income calculation (from BOQItems)
        total_p_income = BOQItem.objects.filter(
            project_id=project_id,
            section=plan.section,
            bill_no=plan.bill_no,
            labour_specification=plan.labour_activity,
        ).aggregate(
            total=Sum(
                F("contract_quantity") * F("contract_rate"),
                output_field=models.DecimalField(),
            )
        )["total"] or Decimal("0")

        days = (plan.finish_date - plan.start_date).days + 1
        daily_p_cost = total_p_cost / Decimal(days) if days > 0 else total_p_cost
        daily_p_income = total_p_income / Decimal(days) if days > 0 else total_p_income

        curr = plan.start_date
        while curr <= plan.finish_date:
            daily_planned_cost[curr] += daily_p_cost
            daily_planned_income[curr] += daily_p_income
            curr += timedelta(days=1)

    # 2. Map Actual Costs
    for entry in entries:
        daily_actual_cost[entry.date] += entry.total_cost

    # 3. Calculate Burn Rate (to date)
    cum_p_cost_today = sum(v for d, v in daily_planned_cost.items() if d <= today)
    cum_a_cost_today = sum(v for d, v in daily_actual_cost.items() if d <= today)

    burn_rate = Decimal("1.0")
    if cum_p_cost_today > 0:
        burn_rate = cum_a_cost_today / cum_p_cost_today

    # 4. Build Monthly Data series
    labels = []
    planned_income = []
    cost_planned = []
    cost_actual = []
    cum_cost_planned = []
    cum_cost_actual = []

    cost_forecast_start_index = -1

    cum_p_cost = Decimal("0.0")
    cum_p_inc = Decimal("0.0")
    cum_a_cost = Decimal("0.0")

    curr = project_start
    month_p_cost = Decimal("0.0")
    month_p_inc = Decimal("0.0")
    month_a_cost = Decimal("0.0")

    # Loop day by day to calculate cumulative values
    while curr <= viz_end_date:
        p_cost = daily_planned_cost.get(curr, Decimal("0.0"))
        p_inc = daily_planned_income.get(curr, Decimal("0.0"))
        a_cost = daily_actual_cost.get(curr, Decimal("0.0"))

        cum_p_cost += p_cost
        cum_p_inc += p_inc

        if curr <= today:
            cum_a_cost += a_cost
            month_a_cost += a_cost
        else:
            # Apply burn rate to future planned costs
            forecast_a_cost = p_cost * Decimal(str(burn_rate))
            cum_a_cost += forecast_a_cost
            month_a_cost += forecast_a_cost

        month_p_cost += p_cost
        month_p_inc += p_inc

        # At the end of the month or at the viz_end_date, snapshot the data
        is_month_end = (curr + timedelta(days=1)).month != curr.month
        is_viz_end = curr == viz_end_date

        if is_month_end or is_viz_end:
            # Only record if within display window
            if curr >= display_start.replace(day=1):
                labels.append(curr.strftime("%b %y"))

                if cost_forecast_start_index == -1 and curr >= today.replace(day=1):
                    cost_forecast_start_index = len(labels) - 1

                # Monthly series
                planned_income.append(float(month_p_inc))
                cost_planned.append(float(month_p_cost))

                # Actual cost is only "actual" up to today, then it's forecast
                if curr < today.replace(day=1):
                    cost_actual.append(float(month_a_cost))
                elif curr.month == today.month and curr.year == today.year:
                    # Current month is a mix, but we'll show it as actual/current
                    cost_actual.append(float(month_a_cost))
                else:
                    cost_actual.append(
                        float(month_a_cost)
                    )  # This is now the forecast portion

                # Cumulative series
                cum_cost_planned.append(float(cum_p_cost))
                cum_cost_actual.append(float(cum_a_cost))

            # Reset monthly counters
            month_p_cost = Decimal("0.0")
            month_p_inc = Decimal("0.0")
            month_a_cost = Decimal("0.0")

        curr += timedelta(days=1)

    # 5. KPIs
    month_start = today.replace(day=1)
    month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

    current_month_actual = sum(
        daily_actual_cost.get(month_start + timedelta(days=i), Decimal("0.0"))
        for i in range((today - month_start).days + 1)
    )
    current_month_planned = sum(
        daily_planned_cost.get(month_start + timedelta(days=i), Decimal("0.0"))
        for i in range((month_end - month_start).days + 1)
    )

    return {
        "labels": labels,
        "planned_income": planned_income,
        "cost_planned": cost_planned,
        "cost_actual": cost_actual,
        "cum_cost_planned": cum_cost_planned,
        "cum_cost_actual": cum_cost_actual,
        "cost_forecast_start_index": cost_forecast_start_index,
        "kpis": {
            "month_actual": float(current_month_actual),
            "month_planned": float(current_month_planned),
            "burn_rate": float(burn_rate),
            "total_budget": float(cum_p_cost),
            "today": today.strftime("%Y-%m-%d"),
            "horizon_label": horizon_type.capitalize(),
        },
    }


def get_project_performance_summary(project_id):
    """
    Calculates high-level project-wide performance indices (PPI, CPI).
    """
    plans = ProductionPlan.objects.filter(project_id=project_id, is_archived=False)
    entries = DailyActivityEntry.objects.filter(project_id=project_id)

    total_planned_qty = plans.aggregate(total=Sum("quantity"))["total"] or Decimal("0")
    total_produced_qty = entries.aggregate(total=Sum("quantity"))["total"] or Decimal(
        "0"
    )

    total_actual_cost = Decimal("0")
    total_actual_hours = Decimal("0")
    for entry in entries:
        total_actual_cost += entry.total_cost
        total_actual_hours += entry.man_hours

    # Planned Totals
    total_planned_cost = Decimal("0")
    total_planned_hours = Decimal("0")
    for plan in plans:
        if plan.labour_activity:
            total_planned_cost += (
                plan.total_labour_cost + plan.total_plant_cost + plan.total_other_cost
            )
            for res in plan.resources.filter(resource_type="LABOUR"):
                total_planned_hours += (res.number or 0) * (res.days or 0) * 8

    # Performance Indices
    ppi = Decimal("1.0")  # Production Performance Index
    if total_planned_hours > 0 and total_planned_qty > 0:
        planned_productivity = total_planned_qty / total_planned_hours
        actual_productivity = (
            total_produced_qty / total_actual_hours if total_actual_hours > 0 else 0
        )
        if planned_productivity > 0:
            ppi = actual_productivity / planned_productivity

    cpi = Decimal("1.0")  # Cost Performance Index
    earned_value = Decimal("0")
    if total_planned_qty > 0:
        earned_value = (total_produced_qty / total_planned_qty) * total_planned_cost

    if total_actual_cost > 0:
        cpi = earned_value / total_actual_cost

    return {
        "total_planned_qty": total_planned_qty,
        "total_produced_qty": total_produced_qty,
        "total_actual_cost": total_actual_cost,
        "total_planned_cost": total_planned_cost,
        "ppi": round(ppi, 2),
        "cpi": round(cpi, 2),
        "overall_progress_pct": round((total_produced_qty / total_planned_qty * 100), 1)
        if total_planned_qty > 0
        else 0,
    }


def get_project_productivity_report_data(
    project_ids, history_horizon="3m", forecast_horizon="3m"
):
    """
    Generates comprehensive data for the Productivity & Cost Report.
    Includes monthly aggregation, multi-horizon forecasts, and activity projections.
    Supports multi-project aggregation for Portfolio Dashboards.
    """
    from datetime import timedelta

    from dateutil.relativedelta import relativedelta

    from app.Estimator.models import BOQItem

    # Handle single project ID or list
    if not isinstance(project_ids, (list, tuple)):
        project_ids = [project_ids]

    summary = get_project_performance_summary(
        project_ids[0]
    )  # Use first for base summary if needed
    plans = ProductionPlan.objects.filter(project_id__in=project_ids, is_archived=False)
    entries = DailyActivityEntry.objects.filter(project_id__in=project_ids)

    if not entries.exists() and not plans.exists():
        return {"summary": summary, "charts": {}, "forecasts": {}, "activities": []}

    today = timezone.now().date()

    # 1. Monthly Aggregation for Charts
    # Map horizons to delta dates
    if history_horizon == "1m":
        start_date = today - relativedelta(months=1)
    elif history_horizon == "3m":
        start_date = today - relativedelta(months=3)
    elif history_horizon == "6m":
        start_date = today - relativedelta(months=6)
    else:  # 'all'
        first_entry = entries.order_by("date").first()
        if first_entry:
            start_date = first_entry.date.replace(day=1)
        else:
            start_date = today - relativedelta(months=6)

    # Forecast end date
    if forecast_horizon == "m":
        end_date = today + relativedelta(months=1)
    elif forecast_horizon == "3m":
        end_date = today + relativedelta(months=3)
    elif forecast_horizon == "6m":
        end_date = today + relativedelta(months=6)
    elif forecast_horizon == "1y":
        end_date = today + relativedelta(years=1)
    else:
        end_date = today + relativedelta(months=3)

    # Monthly buckets
    monthly_data = {}
    curr = start_date.replace(day=1)
    while curr <= end_date:
        monthly_data[curr.strftime("%Y-%m")] = {
            "label": curr.strftime("%b %y"),
            "planned_qty": Decimal("0"),
            "actual_qty": Decimal("0"),
            "planned_cost": Decimal("0"),
            "actual_cost": Decimal("0"),
            "planned_revenue": Decimal("0"),
            "actual_revenue": Decimal("0"),
            "actual_hours": Decimal("0"),
        }
        curr += relativedelta(months=1)

    # Initial cumulative totals (Pre-window)
    running_p_prod = Decimal("0")
    running_a_prod = Decimal("0")

    # Fill Planned (Distributed linearly across duration)
    for plan in plans:
        # Get Contract Rate for Revenue
        boq_item = BOQItem.objects.filter(
            project_id=plan.project_id,
            labour_specification=plan.labour_activity,
            section=plan.section,
            bill_no=plan.bill_no,
        ).first()
        contract_rate = boq_item.contract_rate if boq_item else Decimal("0")

        if plan.start_date and plan.finish_date:
            duration_days = (plan.finish_date - plan.start_date).days + 1
            if duration_days <= 0:
                continue

            daily_qty = plan.quantity / Decimal(duration_days)
            total_p_cost = (
                plan.total_labour_cost + plan.total_plant_cost + plan.total_other_cost
            )
            daily_cost = total_p_cost / Decimal(duration_days)
            daily_rev = daily_qty * contract_rate

            p_curr = plan.start_date
            while p_curr <= plan.finish_date:
                if p_curr < start_date:
                    running_p_prod += daily_qty
                else:
                    month_key = p_curr.strftime("%Y-%m")
                    if month_key in monthly_data:
                        monthly_data[month_key]["planned_qty"] += daily_qty
                        monthly_data[month_key]["planned_cost"] += daily_cost
                        monthly_data[month_key]["planned_revenue"] += daily_rev
                p_curr += timedelta(days=1)

    # Fill Actuals
    for entry in entries:
        # Get Contract Rate for Revenue (per entry/plan)
        boq_item = BOQItem.objects.filter(
            project_id=entry.project_id,
            labour_specification=entry.production_plan.labour_activity,
            section=entry.production_plan.section,
            bill_no=entry.production_plan.bill_no,
        ).first()
        contract_rate = boq_item.contract_rate if boq_item else Decimal("0")
        actual_rev = entry.quantity * contract_rate

        if entry.date < start_date:
            running_a_prod += entry.quantity
        else:
            month_key = entry.date.strftime("%Y-%m")
            if month_key in monthly_data:
                monthly_data[month_key]["actual_qty"] += entry.quantity
                monthly_data[month_key]["actual_cost"] += entry.total_cost
                monthly_data[month_key]["actual_revenue"] += actual_rev
                monthly_data[month_key]["actual_hours"] += entry.man_hours

    # 2. Build Chart Series
    sorted_months = sorted(monthly_data.keys())
    labels = []
    prod_planned = []
    prod_actual = []
    cost_planned = []
    cost_actual = []
    productivity_actual = []  # Qty / Hours

    cum_prod_planned = []
    cum_prod_actual = []
    cum_cost_planned = []
    cum_cost_actual = []
    cum_profit_planned = []
    cum_profit_actual = []

    running_p_prod = Decimal("0")
    running_a_prod = Decimal("0")
    running_p_cost = Decimal("0")
    running_a_cost = Decimal("0")
    running_p_rev = Decimal("0")
    running_a_rev = Decimal("0")

    forecast_start_idx = 0
    found_forecast = False

    for i, m_key in enumerate(sorted_months):
        data = monthly_data[m_key]
        labels.append(data["label"])

        # Monthly Incremental
        prod_planned.append(float(data["planned_qty"]))
        cost_planned.append(float(data["planned_cost"]))

        # S-Curve Cumulative
        running_p_prod += data["planned_qty"]
        running_p_cost += data["planned_cost"]
        running_p_rev += data["planned_revenue"]

        cum_prod_planned.append(float(running_p_prod))
        cum_cost_planned.append(float(running_p_cost))
        cum_profit_planned.append(float(running_p_rev - running_p_cost))

        # Handle Actuals vs Forecast
        is_past = m_key <= today.strftime("%Y-%m")
        if is_past:
            prod_actual.append(float(data["actual_qty"]))
            cost_actual.append(float(data["actual_cost"]))
            running_a_prod += data["actual_qty"]
            running_a_cost += data["actual_cost"]
            running_a_rev += data["actual_revenue"]

            cum_prod_actual.append(float(running_a_prod))
            cum_cost_actual.append(float(running_a_cost))
            cum_profit_actual.append(float(running_a_rev - running_a_cost))

            hours = data["actual_hours"]
            productivity_actual.append(
                float(data["actual_qty"] / hours) if hours > 0 else 0
            )
        else:
            if not found_forecast:
                forecast_start_idx = i
                found_forecast = True

            # In forecasting range
            prod_actual.append(None)
            cost_actual.append(None)
            cum_prod_actual.append(None)
            cum_cost_actual.append(None)
            cum_profit_actual.append(None)
            productivity_actual.append(None)

    # 3. Multi-Horizon Forecasts
    ppi = summary["ppi"]

    def get_planned_in_range(start, end):
        total = Decimal("0")
        for plan in plans:
            if plan.start_date and plan.finish_date:
                overlap_start = max(plan.start_date, start)
                overlap_end = min(plan.finish_date, end)
                if overlap_start <= overlap_end:
                    overlap_days = (overlap_end - overlap_start).days + 1
                    total_p_days = (plan.finish_date - plan.start_date).days + 1
                    total += (plan.quantity / Decimal(total_p_days)) * Decimal(
                        overlap_days
                    )
        return total

    horizons = {
        "next_month": today + relativedelta(months=1),
        "term": today + relativedelta(months=3),
        "half_year": today + relativedelta(months=6),
        "year": today + relativedelta(years=1),
    }

    forecasts = {}
    for key, date_limit in horizons.items():
        planned_qty_future = get_planned_in_range(today + timedelta(days=1), date_limit)
        forecasts[key] = {
            "planned_qty": float(planned_qty_future),
            "forecast_qty": float(planned_qty_future * ppi),
            "accuracy_factor": float(ppi),
        }

    # 4. Activity Specific Projections
    activity_projections = []
    for plan in plans.filter(finish_date__gte=today).order_by("finish_date")[:10]:
        plan_actual_qty = entries.filter(production_plan=plan).aggregate(
            total=Sum("quantity")
        )["total"] or Decimal("0")
        remaining_qty = max(Decimal("0"), plan.quantity - plan_actual_qty)

        if remaining_qty > 0:
            current_daily_rate = plan.daily_rate * ppi
            if current_daily_rate > 0:
                est_days_remaining = remaining_qty / current_daily_rate
                est_finish_date = today + timedelta(days=int(est_days_remaining))
            else:
                est_finish_date = plan.finish_date

            variance_days = (est_finish_date - plan.finish_date).days

            activity_projections.append(
                {
                    "activity": plan.activity,
                    "section": plan.section,
                    "bill_no": plan.bill_no,
                    "planned_finish": plan.finish_date,
                    "estimated_finish": est_finish_date,
                    "variance_days": variance_days,
                    "status": "Delayed" if variance_days > 0 else "On track",
                    "status_color": "rose" if variance_days > 0 else "emerald",
                    "remaining_qty": float(remaining_qty),
                    "unit": plan.unit_display,
                }
            )

    return {
        "summary": summary,
        "charts": {
            "labels": labels,
            "prod_planned": prod_planned,
            "prod_actual": prod_actual,
            "cost_planned": cost_planned,
            "cost_actual": cost_actual,
            "productivity_actual": productivity_actual,
            "cum_prod_planned": cum_prod_planned,
            "cum_prod_actual": cum_prod_actual,
            "cum_cost_planned": cum_cost_planned,
            "cum_cost_actual": cum_cost_actual,
            "cum_profit_planned": cum_profit_planned,
            "cum_profit_actual": cum_profit_actual,
            "forecast_start_index": forecast_start_idx,
        },
        "forecasts": forecasts,
        "activities": activity_projections,
    }


def get_premium_productivity_report_data(project_id, active_only=False, horizon="ptd"):
    """
    Calculates PPI, CPI, and Impact metrics based on Excel logic.
    Groups results by Section and Bill with weighted averages.
    """
    import json
    from collections import defaultdict

    today = timezone.now().date()

    # S-Curve Window logic
    if horizon == "daily":
        start_window = today
        end_window = today
    elif horizon == "weekly":
        start_window = today - timedelta(days=today.weekday())
        end_window = start_window + timedelta(days=6)
    elif horizon == "mtd":
        start_window = today.replace(day=1)
        end_window = (start_window + relativedelta(months=1)) - timedelta(days=1)
    else:  # ptd
        first_entry = (
            DailyActivityEntry.objects.filter(project_id=project_id)
            .order_by("date")
            .first()
        )
        start_window = first_entry.date if first_entry else today
        end_window = today

    date_range = [
        start_window + timedelta(days=i)
        for i in range((end_window - start_window).days + 1)
    ]

    daily_planned_qty = defaultdict(Decimal)
    daily_planned_cost = defaultdict(Decimal)
    daily_planned_revenue = defaultdict(Decimal)
    daily_actual_qty = defaultdict(Decimal)
    daily_actual_cost = defaultdict(Decimal)
    daily_actual_revenue = defaultdict(Decimal)

    # Define date filters based on horizon
    date_filter = {}
    if horizon == "daily":
        date_filter["date"] = today
    elif horizon == "weekly":
        start_of_week = today - timedelta(days=today.weekday())
        date_filter["date__gte"] = start_of_week
    elif horizon == "mtd":
        date_filter["date__gte"] = today.replace(day=1)

    plans_query = ProductionPlan.objects.filter(
        project_id=project_id, is_archived=False, is_leaf=True
    )

    if active_only:
        plans_query = plans_query.filter(finish_date__gte=today, start_date__lte=today)

    plans = plans_query.select_related("labour_activity").prefetch_related("resources")

    # Group activities by Section > Bill
    hierarchy = defaultdict(lambda: defaultdict(list))

    # Project-wide aggregates
    p_total_weight = Decimal("0")
    p_total_weighted_ppi = Decimal("0")
    p_total_weighted_cpi = Decimal("0")
    p_total_days_impact = Decimal("0")
    p_total_cost_impact = Decimal("0")

    for plan in plans:
        # 1. Table Data Calculations (PTD)
        entries_query = DailyActivityEntry.objects.filter(
            production_plan=plan, **date_filter
        )
        if not entries_query.exists() and horizon != "ptd":
            continue

        # For calculation, we want history up to today
        all_history = DailyActivityEntry.objects.filter(
            production_plan=plan, date__lte=today
        )

        total_qty = entries_query.aggregate(total=Sum("quantity"))["total"] or Decimal(
            "0"
        )
        total_cost = sum((e.total_cost for e in all_history), Decimal("0"))
        total_days = all_history.values("date").distinct().count()

        # Target Values
        target_prod_rate = plan.daily_rate
        budgeted_cost = (
            plan.total_labour_cost + plan.total_plant_cost + plan.total_other_cost
        )
        target_unit_cost = (
            plan.budget_unit_rate
            if hasattr(plan, "budget_unit_rate")
            else (budgeted_cost / plan.quantity if plan.quantity > 0 else Decimal("0"))
        )

        # Get Contract Rate for Revenue
        from app.Estimator.models import BOQItem

        boq_item = BOQItem.objects.filter(
            project_id=project_id,
            labour_specification=plan.labour_activity,
            section=plan.section,
            bill_no=plan.bill_no,
        ).first()
        contract_rate = boq_item.contract_rate if boq_item else Decimal("0")

        # 2. S-Curve Data Aggregation (Within Window)
        # Planned
        if plan.start_date and plan.finish_date:
            plan_days = (plan.finish_date - plan.start_date).days + 1
            if plan_days > 0:
                day_qty = plan.quantity / Decimal(plan_days)
                day_cost = budgeted_cost / Decimal(plan_days)
                day_rev = day_qty * contract_rate

                curr_p = max(plan.start_date, start_window)
                end_p = min(plan.finish_date, end_window)
                while curr_p <= end_p:
                    daily_planned_qty[curr_p] += day_qty
                    daily_planned_cost[curr_p] += day_cost
                    daily_planned_revenue[curr_p] += day_rev
                    curr_p += timedelta(days=1)

        # Actual (Within Window)
        window_entries = DailyActivityEntry.objects.filter(
            production_plan=plan,
            date__gte=start_window,
            date__lte=end_window,
        )
        for entry in window_entries:
            daily_actual_qty[entry.date] += entry.quantity
            daily_actual_cost[entry.date] += entry.total_cost
            daily_actual_revenue[entry.date] += entry.quantity * contract_rate

        # Actual Values for Table
        actual_prod_rate = (
            total_qty / Decimal(total_days) if total_days > 0 else Decimal("0")
        )
        actual_unit_cost = total_cost / total_qty if total_qty > 0 else Decimal("0")

        # Indices
        ppi = (
            actual_prod_rate / target_prod_rate
            if target_prod_rate > 0
            else Decimal("0")
        )
        cpi = (
            target_unit_cost / actual_unit_cost
            if actual_unit_cost > 0
            else Decimal("0")
        )

        # Impact (always PTD based)
        duration_days = (
            (plan.finish_date - plan.start_date).days + 1
            if plan.start_date and plan.finish_date
            else 0
        )
        duration = Decimal(duration_days)
        # Days Impact: (Duration / PPI) - Duration (Positive = Delay)
        days_affected = (duration / ppi) - duration if ppi > 0 else Decimal("0")
        # Financial Impact: (Budgeted Cost / CPI) - Budgeted Cost (Positive = Loss)
        cost_impact = (budgeted_cost / cpi) - budgeted_cost if cpi > 0 else Decimal("0")

        # Threshold Colors: Higher is better
        ppi_color = "emerald"
        if ppi < 0.8:
            ppi_color = "rose"
        elif ppi < 1.0:
            ppi_color = "amber"

        cpi_color = "emerald"
        if cpi < 0.9:
            cpi_color = "rose"
        elif cpi < 1.0:
            cpi_color = "amber"

        # Trend Data (Last 10 entries)
        trend_labels, trend_ppi, trend_cpi = [], [], []
        trend_act_prod, trend_tgt_prod = [], []
        trend_act_cost, trend_tgt_cost = [], []

        last_entries = all_history.order_by("-date")[:10][::-1]
        for e in last_entries:
            trend_labels.append(e.date.strftime("%d %b"))
            # Indices: Higher is better (Actual / Target)
            d_ppi = e.quantity / target_prod_rate if target_prod_rate > 0 else 0
            d_cpi = (
                target_unit_cost / (e.total_cost / e.quantity)
                if e.quantity > 0 and e.total_cost > 0
                else 0
            )
            trend_ppi.append(float(d_ppi))
            trend_cpi.append(float(d_cpi))
            # Raw Values
            trend_act_prod.append(float(e.quantity))
            trend_tgt_prod.append(float(target_prod_rate))
            trend_act_cost.append(
                float(e.total_cost / e.quantity if e.quantity > 0 else 0)
            )
            trend_tgt_cost.append(float(target_unit_cost))

        act_data = {
            "id": plan.id,
            "activity": plan.activity,
            "unit": plan.unit_display,
            "target_prod": float(target_prod_rate),
            "actual_prod": float(actual_prod_rate),
            "target_cost": float(target_unit_cost),
            "actual_cost": float(actual_unit_cost),
            "ppi": float(ppi),
            "ppi_color": ppi_color,
            "cpi": float(cpi),
            "cpi_color": cpi_color,
            "days_affected": float(days_affected),
            "cost_impact": float(cost_impact),
            "progress": float(plan.progress_percentage),
            "budgeted_cost": float(budgeted_cost),
            "trend": {
                "labels": trend_labels,
                "ppi": trend_ppi,
                "cpi": trend_cpi,
                "act_prod": trend_act_prod,
                "tgt_prod": trend_tgt_prod,
                "act_cost": trend_act_cost,
                "tgt_cost": trend_tgt_cost,
            },
        }

        hierarchy[plan.section or "Uncategorized"][plan.bill_no or "General"].append(
            act_data
        )

        # Aggregates for Global Summary
        p_total_weight += budgeted_cost
        p_total_weighted_ppi += ppi * budgeted_cost
        p_total_weighted_cpi += cpi * budgeted_cost
        p_total_days_impact += days_affected
        p_total_cost_impact += cost_impact

    # Post-process hierarchy for weighted averages
    sections_list = []
    for section_name, bills in hierarchy.items():
        s_weight, s_ppi_sum, s_cpi_sum, s_days, s_cost = (
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        )
        bills_list = []

        for bill_no, activities in bills.items():
            b_weight, b_ppi_sum, b_cpi_sum, b_days, b_cost = (
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
            )
            for a in activities:
                w = Decimal(str(a["budgeted_cost"]))
                b_weight += w
                b_ppi_sum += Decimal(str(a["ppi"])) * w
                b_cpi_sum += Decimal(str(a["cpi"])) * w
                b_days += Decimal(str(a["days_affected"]))
                b_cost += Decimal(str(a["cost_impact"]))

            bills_list.append(
                {
                    "number": bill_no,
                    "activities": activities,
                    "ppi": float(b_ppi_sum / b_weight) if b_weight > 0 else 0,
                    "cpi": float(b_cpi_sum / b_weight) if b_weight > 0 else 0,
                    "days_affected": float(b_days),
                    "cost_impact": float(b_cost),
                }
            )

            s_weight += b_weight
            s_ppi_sum += b_ppi_sum
            s_cpi_sum += b_cpi_sum
            s_days += b_days
            s_cost += b_cost

        sections_list.append(
            {
                "name": section_name,
                "bills": bills_list,
                "ppi": float(s_ppi_sum / s_weight) if s_weight > 0 else 0,
                "cpi": float(s_cpi_sum / s_weight) if s_weight > 0 else 0,
                "days_affected": float(s_days),
                "cost_impact": float(s_cost),
            }
        )

    # 3. Finalize S-Curve Data
    labels = []
    planned_qty_series = []
    planned_cost_series = []
    planned_profit_series = []
    actual_qty_series = []
    actual_cost_series = []
    actual_profit_series = []

    cum_planned_qty = Decimal("0")
    cum_planned_cost = Decimal("0")
    cum_planned_rev = Decimal("0")
    cum_actual_qty = Decimal("0")
    cum_actual_cost = Decimal("0")
    cum_actual_rev = Decimal("0")

    for d in date_range:
        labels.append(d.strftime("%d %b"))
        cum_planned_qty += daily_planned_qty[d]
        cum_planned_cost += daily_planned_cost[d]
        cum_planned_rev += daily_planned_revenue[d]

        planned_qty_series.append(float(cum_planned_qty))
        planned_cost_series.append(float(cum_planned_cost))
        planned_profit_series.append(float(cum_planned_rev - cum_planned_cost))

        if d <= today:
            cum_actual_qty += daily_actual_qty[d]
            cum_actual_cost += daily_actual_cost[d]
            cum_actual_rev += daily_actual_revenue[d]
            actual_qty_series.append(float(cum_actual_qty))
            actual_cost_series.append(float(cum_actual_cost))
            actual_profit_series.append(float(cum_actual_rev - cum_actual_cost))
        else:
            actual_qty_series.append(None)
            actual_cost_series.append(None)
            actual_profit_series.append(None)

    charts_json = {
        "labels": labels,
        "cum_prod_planned": planned_qty_series,
        "cum_prod_actual": actual_qty_series,
        "cum_cost_planned": planned_cost_series,
        "cum_cost_actual": actual_cost_series,
        "cum_profit_planned": planned_profit_series,
        "cum_profit_actual": actual_profit_series,
        "datasets": [
            {
                "label": "Planned Qty",
                "data": planned_qty_series,
                "borderColor": "rgb(79, 70, 229)",  # indigo-600
                "backgroundColor": "rgba(79, 70, 229, 0.1)",
                "yAxisID": "y",
                "tension": 0.4,
                "fill": False,
            },
            {
                "label": "Actual Qty",
                "data": actual_qty_series,
                "borderColor": "rgb(4, 120, 87)",  # emerald-700
                "backgroundColor": "rgba(4, 120, 87, 0.1)",
                "yAxisID": "y",
                "tension": 0.4,
                "fill": False,
            },
            {
                "label": "Planned Cost",
                "data": planned_cost_series,
                "borderColor": "rgba(79, 70, 229, 0.4)",
                "borderDash": [5, 5],
                "yAxisID": "y1",
                "tension": 0.4,
                "fill": False,
                "borderWidth": 2,
            },
            {
                "label": "Actual Cost",
                "data": actual_cost_series,
                "borderColor": "rgba(4, 120, 87, 0.4)",
                "borderDash": [5, 5],
                "yAxisID": "y1",
                "tension": 0.4,
                "fill": False,
                "borderWidth": 2,
            },
            {
                "label": "Planned Profit",
                "data": planned_profit_series,
                "borderColor": "#10b981",  # emerald-500
                "borderWidth": 2,
                "yAxisID": "y1",
                "tension": 0.4,
                "fill": False,
            },
            {
                "label": "Actual Profit",
                "data": actual_profit_series,
                "borderColor": "#059669",  # emerald-600
                "borderWidth": 3,
                "yAxisID": "y1",
                "tension": 0.4,
                "fill": False,
            },
        ],
        "today_index": date_range.index(today) if today in date_range else -1,
    }

    return {
        "summary": {
            "ppi": float(p_total_weighted_ppi / p_total_weight)
            if p_total_weight > 0
            else 0,
            "cpi": float(p_total_weighted_cpi / p_total_weight)
            if p_total_weight > 0
            else 0,
            "days_impact": float(p_total_days_impact),
            "cost_impact": float(p_total_cost_impact),
        },
        "sections": sections_list,
        "charts_json": json.dumps(charts_json),
    }


def get_activity_financial_summary(
    project_id, f_section=None, f_bill=None, f_activity=None
):
    """
    Centralized logic to group BOQItems into Activities (Section > Bill > Act Name).
    Applies the 'Labour Priority' rule for quantities and uses subqueries for plant costs
     to avoid Cartesian product duplication.
    """

    from django.db.models.functions import Trim

    # 1. Base Queryset with Coalesced names and units
    queryset = (
        BOQItem.objects.filter(project_id=project_id, is_section_header=False)
        .filter(
            models.Q(labour_specification__isnull=False)
            | models.Q(plant_specification__isnull=False)
        )
        .annotate(
            clean_section=Trim(Coalesce("section", Value(""))),
            clean_bill=Trim(Coalesce("bill_no", Value(""))),
            act_name=Trim(
                Coalesce("labour_specification__name", "plant_specification__name")
            ),
            act_unit=Coalesce(
                "labour_specification__unit", "plant_specification__unit"
            ),
        )
    )

    # 2. Apply optional filters
    if f_section:
        queryset = queryset.filter(clean_section=f_section)
    if f_bill:
        queryset = queryset.filter(clean_bill=f_bill)
    if f_activity:
        queryset = queryset.filter(act_name__icontains=f_activity)

    # 3. Aggregation with Priority Logic
    grouped_queryset = (
        queryset.values(
            act_section=F("clean_section"),
            act_bill=F("clean_bill"),
            act_name=F("act_name"),
            act_unit=F("act_unit"),
        )
        .annotate(
            # Pick one labour_specification id per group for linking
            labour_spec_id=Max("labour_specification"),
            num_items=Count("id"),
            # Total Tracker: Sum contract_quantity with Labour Priority logic
            total_tracker=Sum(
                Case(
                    When(
                        unit=F("act_unit"),
                        labour_specification__isnull=False,
                        then=F("contract_quantity"),
                    ),
                    When(
                        unit=F("act_unit"),
                        labour_specification__isnull=True,
                        plant_specification__isnull=False,
                        then=F("contract_quantity"),
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            ),
            total_amount=Sum(
                F("contract_quantity") * F("contract_rate"),
                output_field=DecimalField(),
            ),
            # Daily labour cost & production base
            daily_labour_cost=Max(
                (
                    Coalesce(F("labour_specification__crew__skilled"), 0)
                    * Coalesce(F("labour_specification__crew__skilled_rate"), 0)
                    + Coalesce(F("labour_specification__crew__semi_skilled"), 0)
                    * Coalesce(F("labour_specification__crew__semi_skilled_rate"), 0)
                    + Coalesce(F("labour_specification__crew__general"), 0)
                    * Coalesce(F("labour_specification__crew__general_rate"), 0)
                )
                * Coalesce(F("crew_count"), 1),
                output_field=DecimalField(),
            ),
            daily_production_base=Max(
                Coalesce(
                    F("labour_specification__daily_production"),
                    F("plant_specification__daily_production"),
                    Value(0),
                )
                * Coalesce(F("crew_count"), 1),
                output_field=DecimalField(),
            ),
            crew_count=Coalesce(
                Max("crew_count"), Value(1), output_field=DecimalField()
            ),
        )
        .annotate(
            duration=Case(
                When(
                    daily_production_base__gt=0,
                    then=Ceil(F("total_tracker") / F("daily_production_base")),
                ),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
    )

    # 4. Plant Subqueries to avoid Join Multiplication
    # We use a nested subquery to find all unique Plant Specification IDs for this group
    # this avoids direct joins to BOQItem in the main subquery which cause multiplication.
    relevant_specs = (
        BOQItem.objects.filter(
            project_id=project_id,
            section=OuterRef(OuterRef("act_section")),
            bill_no=OuterRef(OuterRef("act_bill")),
            is_section_header=False,
        )
        .filter(
            models.Q(labour_specification__name=OuterRef(OuterRef("act_name")))
            | models.Q(plant_specification__name=OuterRef(OuterRef("act_name")))
        )
        .values("plant_specification")
    )

    plant_cost_subquery = (
        ProjectPlantSpecificationComponent.objects.filter(
            specification_id__in=Subquery(relevant_specs)
        )
        .order_by()
        .values("specification__project_id")
        .annotate(total_rate=Sum("plant_type__hourly_rate"))
        .values("total_rate")
    )

    plant_count_subquery = (
        ProjectPlantSpecificationComponent.objects.filter(
            specification_id__in=Subquery(relevant_specs)
        )
        .order_by()
        .values("specification__project_id")
        .annotate(cnt=Count("plant_type", distinct=True))
        .values("cnt")
    )

    final_queryset = (
        grouped_queryset.annotate(
            daily_plant_cost_base=Coalesce(
                Subquery(plant_cost_subquery, output_field=DecimalField()),
                Value(0),
                output_field=DecimalField(),
            ),
            plant_count_base=Coalesce(
                Subquery(plant_count_subquery, output_field=DecimalField()),
                Value(0),
                output_field=DecimalField(),
            ),
        )
        .annotate(
            daily_plant_cost=F("daily_plant_cost_base") * F("crew_count"),
            plant_count=F("plant_count_base") * F("crew_count"),
        )
        .annotate(total_daily_cost=F("daily_labour_cost") + F("daily_plant_cost"))
    )

    return final_queryset.order_by("act_section", "act_bill", "act_name")
