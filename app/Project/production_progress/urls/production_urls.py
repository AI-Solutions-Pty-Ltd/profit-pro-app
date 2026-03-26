from django.urls import path
from ..views import production_views as views

urlpatterns = [
    path(
        "<int:project_pk>/dashboard/",
        views.ProductionDashboardView.as_view(),
        name="production-dashboard",
    ),
    path(
        "<int:project_pk>/planning/",
        views.ProductionPlanningView.as_view(),
        name="production-planning",
    ),
    path(
        "<int:project_pk>/cost-breakdown/",
        views.ProductionCostBreakdownView.as_view(),
        name="production-cost-breakdown",
    ),
    path(
        "<int:project_pk>/plan/<int:pk>/",
        views.ProductionPlanDetailView.as_view(),
        name="production-plan-detail",
    ),
    path(
        "<int:project_pk>/plan/<int:pk>/edit/",
        views.ProductionPlanUpdateView.as_view(),
        name="production-plan-edit",
    ),
    path(
        "<int:project_pk>/plan/<int:pk>/delete/",
        views.ProductionPlanDeleteView.as_view(),
        name="production-plan-delete",
    ),
    path(
        "<int:project_pk>/create/",
        views.DailyProductionCreateView.as_view(),
        name="production-create",
    ),
    path(
        "<int:project_pk>/logs/",
        views.DailyProductionListView.as_view(),
        name="production-list",
    ),
]
