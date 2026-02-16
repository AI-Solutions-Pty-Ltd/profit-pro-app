"""URL configuration for Company views."""

from django.urls import path

from app.Project.views.company_views import (
    CompanyDetailView,
    CompanyListView,
    CompanyUpdateView,
)

urlpatterns = [
    path("company/list/", CompanyListView.as_view(), name="company-list"),
    path("company/<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
    path(
        "company/<int:pk>/update/", CompanyUpdateView.as_view(), name="company-update"
    ),
]
