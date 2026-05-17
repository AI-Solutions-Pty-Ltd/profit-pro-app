"""URL configuration for Project Documents."""

from django.urls import path

from app.Project.views import document_views

_path_prefix = "document/"

urlpatterns = [
    # Drawing Routes
    path(
        "<int:project_pk>/drawings/",
        document_views.DrawingListView.as_view(),
        name="drawing-list",
    ),
    path(
        "<int:project_pk>/drawings/add/",
        document_views.DrawingCreateView.as_view(),
        name="drawing-create",
    ),
    path(
        "<int:project_pk>/drawings/<int:pk>/edit/",
        document_views.DrawingUpdateView.as_view(),
        name="drawing-update",
    ),
    path(
        "<int:project_pk>/drawings/<int:pk>/delete/",
        document_views.DrawingDeleteView.as_view(),
        name="drawing-delete",
    ),
    # Generic Document Routes
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
