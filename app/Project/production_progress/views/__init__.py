from .dashboard_views import (
    PlanProductivityDashboardView,
    ProductionActivityDetailView,
    ProductionDashboardView,
    ProductionProgressDashboardView,
)
from .planning_views import (
    PlanResourcesAjaxView,
    ProductionCostBreakdownView,
    ProductionPlanDeleteView,
    ProductionPlanDetailView,
    ProductionPlanningView,
    ProductionPlanUpdateView,
    ProductionResourceCreateView,
)
from .productivity_views import (
    DailyProductionCreateView,
    DailyProductivityCreateView,
)
from .reports_views import (
    ProductionForecastDashboardView,
    ProductivityLogsView,
)
from .tracking_views import ProgressTrackingView

__all__ = [
    "ProductionDashboardView",
    "ProductionProgressDashboardView",
    "ProductionActivityDetailView",
    "PlanProductivityDashboardView",
    "ProductionPlanningView",
    "ProductionPlanDetailView",
    "ProductionPlanUpdateView",
    "ProductionPlanDeleteView",
    "ProductionCostBreakdownView",
    "ProductionResourceCreateView",
    "PlanResourcesAjaxView",
    "DailyProductionCreateView",
    "DailyProductivityCreateView",
    "ProductivityLogsView",
    "ProductionForecastDashboardView",
    "ProgressTrackingView",
]
