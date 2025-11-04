from django.urls import path

from .views_reports import (
    ComplianceView,
    CostPerformanceView,
    DashboardView,
    SchedulePerformanceView,
)

app_name = "account"

reports_urls = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("cost-performance/", CostPerformanceView.as_view(), name="cost_performance"),
    path(
        "schedule-performance/",
        SchedulePerformanceView.as_view(),
        name="schedule_performance",
    ),
    path("compliance/", ComplianceView.as_view(), name="compliance"),
]

urlpatterns = reports_urls
