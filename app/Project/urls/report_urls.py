from django.urls import path

from app.Project.views import (
    report_views,
)

urlpatterns = [
    # Project Contractual Report
    path(
        "project/<int:project_pk>/contractual/",
        report_views.ContractualReportView.as_view(),
        name="contractual-report",
    ),
    path(
        "project/<int:project_pk>/contractors/",
        report_views.ContractorsReportView.as_view(),
        name="contractors-report",
    ),
    path(
        "project/<int:project_pk>/construction-progress/",
        report_views.ConstructionProgressReportView.as_view(),
        name="construction-progress-report",
    ),
    # Portfolio Reports
    path(
        "portfolio/reports/financial/",
        report_views.FinancialReportView.as_view(),
        name="portfolio-financial-report",
    ),
    path(
        "portfolio/reports/schedule/",
        report_views.ScheduleReportView.as_view(),
        name="portfolio-schedule-report",
    ),
    path(
        "portfolio/reports/cashflow/",
        report_views.CashflowReportView.as_view(),
        name="portfolio-cashflow-report",
    ),
    path(
        "portfolio/reports/trend/",
        report_views.TrendReportView.as_view(),
        name="portfolio-trend-report",
    ),
]
