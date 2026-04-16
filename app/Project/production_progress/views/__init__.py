from .dashboard_views import (
    PlanProductivityDashboardView,
    ProductionActivityDetailView,
    ProductionDashboardView,
    ProductionProgressDashboardView,
)
from .planning_views import (
    PlanResourcesAjaxView,
    ProductionCostBreakdownDetailView,
    ProductionCostBreakdownView,
    ProductionPlanAjaxDetailView,
    ProductionPlanCreateView,
    ProductionPlanDeleteView,
    ProductionPlanDetailView,
    ProductionPlanGanttView,
    ProductionPlanListView,
    ProductionPlanUpdateView,
    ProductionResourceCreateView,
    GetProjectBillsAjaxView,
    GetProjectItemsAjaxView,
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
from .activity_views import (
    LaborActivityListView,
    LaborActivityDetailView,
    GetProjectLaborActivitiesAjaxView,
)


__all__ = [
    "ProductionDashboardView",
    "ProductionProgressDashboardView",
    "ProductionActivityDetailView",
    "PlanProductivityDashboardView",
    "ProductionPlanCreateView",
    "ProductionPlanGanttView",
    "ProductionPlanListView",
    "ProductionPlanDetailView",
    "ProductionPlanUpdateView",
    "ProductionPlanDeleteView",
    "ProductionCostBreakdownView",
    "ProductionCostBreakdownDetailView",
    "ProductionResourceCreateView",
    "PlanResourcesAjaxView",
    "DailyProductionCreateView",
    "DailyProductivityCreateView",
    "ProductivityLogsView",
    "ProductionForecastDashboardView",
    "ProgressTrackingView",
    "ProductionPlanAjaxDetailView",
    "GetProjectBillsAjaxView",
    "GetProjectItemsAjaxView",
    "LaborActivityListView",
    "LaborActivityDetailView",
    "GetProjectLaborActivitiesAjaxView",
]
