"""URL configuration for Project Documents."""

from django.urls import path

from app.Project.views import document_views

document_urls = [
    path(
        "project/<int:project_pk>/documents/<str:category>/",
        document_views.DocumentListView.as_view(),
        name="document-list",
    ),
    path(
        "project/<int:project_pk>/documents/<str:category>/upload/",
        document_views.DocumentCreateView.as_view(),
        name="document-upload",
    ),
    path(
        "project/<int:project_pk>/documents/<str:category>/<int:pk>/delete/",
        document_views.DocumentDeleteView.as_view(),
        name="document-delete",
    ),
]
