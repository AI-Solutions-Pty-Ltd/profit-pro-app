from django.urls import path

from app.Project.views import (
    portfolio_views,
)

urlpatterns = [
    path(
        "portfolio/dashboard/",
        portfolio_views.PortfolioDashboardView.as_view(),
        name="portfolio-dashboard",
    ),
    path(
        "portfolio/company-dashboard/",
        portfolio_views.CompanyDashboardView.as_view(),
        name="company-dashboard",
    ),
    # New Portfolio Reports
    path(
        "portfolio/reports/compliance/",
        portfolio_views.ComplianceReportView.as_view(),
        name="compliance-report",
    ),
    path(
        "portfolio/reports/impact/",
        portfolio_views.ImpactReportView.as_view(),
        name="impact-report",
    ),
    path(
        "portfolio/reports/risk/",
        portfolio_views.RiskReportView.as_view(),
        name="risk-report",
    ),
]
