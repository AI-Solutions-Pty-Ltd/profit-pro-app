"""URL configuration for Company views."""

from django.urls import path

from . import company_views as cvs

_path_prefix = "company/"

urlpatterns = [
    path(
        "<int:pk>/",
        cvs.CompanyDetailDashboardView.as_view(),
        name="company-detail-dashboard",
    ),
    path(
        "<int:pk>/management/",
        cvs.CompanyManagementView.as_view(),
        name="company-management",
    ),
    path(
        "<int:pk>/reports/<slug:report>/",
        cvs.CompanyReportView.as_view(),
        name="company-report",
    ),
    path(
        "<int:pk>/update/",
        cvs.CompanyUpdateView.as_view(),
        name="company-update",
    ),
    path(
        "<int:pk>/business-setup/",
        cvs.BusinessSetupView.as_view(),
        name="business-setup",
    ),
    path("list/", cvs.CompanyListView.as_view(), name="company-list"),
    path(
        "dashboard/",
        cvs.CompanyDashboardView.as_view(),
        name="company-dashboard",
    ),
    path(
        "<int:pk>/master-dashboard/",
        cvs.MasterProjectDashboardView.as_view(),
        name="master-project-dashboard",
    ),
    path(
        "portfolio-master-dashboard/",
        cvs.MasterPortfolioDashboardView.as_view(),
        name="master-portfolio-dashboard",
    ),
]
