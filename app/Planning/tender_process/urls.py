"""URL configuration for Planning & Procurement app."""

from django.urls import path

from .views import (
    TenderProcessOverviewView,
    TenderProcessSectionCompleteAPIView,
)

_app_name = "planning"

urlpatterns = [
    # Overview Pages
    path(
        "<int:project_pk>/overview/tender-process/",
        TenderProcessOverviewView.as_view(),
        name="tender-process-overview",
    ),
    path(
        "<int:project_pk>/overview/tender-process/api/work-packages/<int:wp_pk>/section-complete/",
        TenderProcessSectionCompleteAPIView.as_view(),
        name="tender-process-section-complete-api",
    ),
]
