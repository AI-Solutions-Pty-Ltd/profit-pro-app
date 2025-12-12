from django.urls import path

from app.Project.views import (
    portfolio_views,
    report_views,
    report_views_portfolio,
    user_management_views,
)

portfolio_urls = [
    path(
        "portfolio/dashboard/",
        portfolio_views.PortfolioDashboardView.as_view(),
        name="portfolio-dashboard",
    ),
    path(
        "portfolio/project-list/",
        portfolio_views.ProjectListView.as_view(),
        name="portfolio-project-list",
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
    # New Portfolio Reports
    path(
        "portfolio/reports/compliance/",
        report_views_portfolio.ComplianceReportView.as_view(),
        name="compliance-report",
    ),
    path(
        "portfolio/reports/impact/",
        report_views_portfolio.ImpactReportView.as_view(),
        name="impact-report",
    ),
    path(
        "portfolio/reports/risk/",
        report_views_portfolio.RiskReportView.as_view(),
        name="risk-report",
    ),
    # User Management - Registers
    path(
        "register/clients/",
        user_management_views.ClientRegisterView.as_view(),
        name="client-register",
    ),
    path(
        "register/clients/<int:pk>/",
        user_management_views.ClientDetailView.as_view(),
        name="client-detail",
    ),
    path(
        "register/signatories/",
        user_management_views.SignatoriesRegisterView.as_view(),
        name="signatory-register",
    ),
]
