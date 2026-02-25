"""URL configuration for Site Management views."""

from django.urls import path

from app.SiteManagement.views import SiteManagementView

app_name = "site_management"

urlpatterns = [
    path(
        "project/<int:pk>/site-management/",
        SiteManagementView.as_view(),
        name="site-management",
    ),
]
