"""URL configuration for Planning & Procurement app."""

from django.urls import path

from .views import (
    TenderDocumentationOverviewView,
    TenderDocumentCreateView,
    TenderDocumentDeleteView,
    TenderDocumentFileUploadView,
    TenderDocumentUpdateView,
)

_app_name = "planning"

urlpatterns = [
    # Overview Pages
    path(
        "<int:project_pk>/overview/tender-documentation/",
        TenderDocumentationOverviewView.as_view(),
        name="tender-documentation-overview",
    ),
    # Tender Documents
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/documents/create/",
        TenderDocumentCreateView.as_view(),
        name="tender-document-create",
    ),
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/documents/<int:pk>/edit/",
        TenderDocumentUpdateView.as_view(),
        name="tender-document-update",
    ),
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/documents/<int:pk>/delete/",
        TenderDocumentDeleteView.as_view(),
        name="tender-document-delete",
    ),
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/documents/<int:doc_pk>/upload/",
        TenderDocumentFileUploadView.as_view(),
        name="tender-document-upload",
    ),
]
