from django.urls import path

from app.Project.views import (
    portfolio_views,
)

urlpatterns = [
    path(
        "dashboard/",
        portfolio_views.PortfolioDashboardView.as_view(),
        name="portfolio-dashboard",
    ),
    path(
        "company-dashboard/",
        portfolio_views.CompanyDashboardView.as_view(),
        name="company-dashboard",
    ),
    # New Portfolio Reports
    path(
        "reports/compliance/",
        portfolio_views.ComplianceReportView.as_view(),
        name="compliance-report",
    ),
    path(
        "reports/impact/",
        portfolio_views.ImpactReportView.as_view(),
        name="impact-report",
    ),
    path(
        "reports/risk/",
        portfolio_views.RiskReportView.as_view(),
        name="risk-report",
    ),
]
