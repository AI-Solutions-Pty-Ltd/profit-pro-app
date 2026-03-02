"""URL configuration for Company views."""

from django.urls import path

from app.Project.views.company_views import (
    CompanyDetailView,
    CompanyListView,
    CompanyUpdateView,
)

_prefix = "company/"

urlpatterns = [
    path("<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
    path("<int:pk>/update/", CompanyUpdateView.as_view(), name="company-update"),
    path("list/", CompanyListView.as_view(), name="company-list"),
]
