"""URL configuration for Company views."""

from django.urls import path

from . import company_views as cvs

_prefix = "company/"

urlpatterns = [
    path("<int:pk>/", cvs.CompanyManagementView.as_view(), name="company-detail"),
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
]
