from django.db.models import Sum, F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from ..models.production_models import (
    ProductionPlan,
    DailyActivityEntry,
    DailyLabourUsage,
    DailyPlantUsage
)
from decimal import Decimal
from collections import defaultdict

def calculate_progress_status(produced, planned, start_date=None, finish_date=None):
    """
    Determines status based on progress vs target and schedule.
    Returns (status_text, color_class)
    """
    if not planned or planned == 0:
        return "Not Planned", "gray"
    
    progress_pct = (Decimal(produced) / Decimal(planned)) * 100
    
    # Check if behind schedule
    is_behind = False
    if finish_date and timezone.now().date() > finish_date and progress_pct < 100:
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
    
    change = ((Decimal(current_umh) - Decimal(previous_umh)) / Decimal(previous_umh)) * 100
    return round(change, 1), change >= 0

def get_dashboard_data(project_id, start_date=None, end_date=None):
    """
    Aggregates all project data for the dashboard with optimized queries.
    """
    plans = ProductionPlan.objects.filter(project_id=project_id)
    entries_qs = DailyActivityEntry.objects.filter(report__project_id=project_id).select_related('report').prefetch_related(
        'labour_usage', 'plant_usage', 'labour_usage__resource', 'plant_usage__resource'
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
    total_planned = plans.aggregate(total=Sum('quantity'))['total'] or 0
    total_produced = sum(entry.quantity for entry in all_entries)
    
    total_spent = Decimal('0.0')
    total_hours = Decimal('0.0')
    
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
        display_spent = round(plan_spent / 1000, 1) if plan_spent >= 1000 else plan_spent
        
        item_cards.append({
            'plan': plan,
            'status_text': status_text,
            'status_color': status_color,
            'day_indicator': day_indicator,
            'completion_pct': min(100, comp_pct),
            'produced_qty': plan_produced,
            'remaining_qty': remaining_qty,
            'spent': display_spent,
            'hours': plan_hours,
            'umh': umh,
            'trend_val': trend_val,
            'trend_positive': trend_positive
        })

    return {
        'total_produced': total_produced,
        'total_planned': total_planned,
        'total_spent': total_spent,
        'total_hours': total_hours,
        'worker_days': worker_days,
        'active_items_count': active_items_count,
        'overall_progress_pct': min(100, overall_progress_pct),
        'status_counts': status_counts,
        'item_cards': item_cards,
    }


def get_activity_detail_data(plan_id):
    """
    Fetches detailed metrics for a single production plan item.
    """
    plan = get_object_or_404(ProductionPlan, pk=plan_id)
    entries = DailyActivityEntry.objects.filter(production_plan=plan).select_related('report').prefetch_related(
        'labour_usage', 'plant_usage', 'labour_usage__resource', 'plant_usage__resource'
    ).order_by('report__date')
    
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
        daily_breakdown.append({
            'day_label': entry.day_number,
            'date': entry.report.date,
            'quantity': entry.quantity,
            'cost': entry.total_cost,
            'hours': entry.man_hours,
            'workers': sum(usage.number for usage in entry.labour_usage.all()),
            'productivity': round(entry.work_productivity, 1),
            'note': entry.report.notes or "",
            'is_latest': (i == len(entry_list) - 1)
        })
        
    return {
        'plan': plan,
        'total_produced': total_produced,
        'total_planned': plan.quantity,
        'completion_pct': min(100, float(completion_pct)),
        'total_spent': total_spent,
        'total_hours': total_hours,
        'worker_days': worker_days,
        'avg_productivity': avg_productivity,
        'cost_per_item': cost_per_item,
        'trend_val': trend_val,
        'trend_positive': trend_positive,
        'status_text': status_text,
        'status_color': status_color,
        'days_active': days_active,
        'daily_breakdown': daily_breakdown,
        'remaining_qty': max(0, plan.quantity - total_produced),
    }
