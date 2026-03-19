"""URL configuration for Project Documents."""

from django.urls import path

from app.Project.views import document_views

_prefix = "document/"

urlpatterns = [
    path(
        "<int:project_pk>/<str:category>/",
        document_views.DocumentListView.as_view(),
        name="document-list",
    ),
    path(
        "<int:project_pk>/<str:category>/upload/",
        document_views.DocumentCreateView.as_view(),
        name="document-upload",
    ),
    path(
        "<int:project_pk>/<str:category>/<int:pk>/edit/",
        document_views.DocumentEditView.as_view(),
        name="document-edit",
    ),
    path(
        "<int:project_pk>/<str:category>/<int:pk>/delete/",
        document_views.DocumentDeleteView.as_view(),
        name="document-delete",
    ),
]
