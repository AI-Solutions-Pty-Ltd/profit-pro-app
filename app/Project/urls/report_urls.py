from django.urls import path

from app.Project.views import (
    report_views,
)

urlpatterns = [
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
