"""URL configuration for Project Stage management."""

from django.urls import path

from app.Project.categories import stage_views

_path_prefix = "stage/"

urlpatterns = [
    path(
        "",
        stage_views.ProjectStageListView.as_view(),
        name="project-stage-list",
    ),
    path(
        "create/",
        stage_views.ProjectStageCreateView.as_view(),
        name="project-stage-create",
    ),
    path(
        "<int:pk>/update/",
        stage_views.ProjectStageUpdateView.as_view(),
        name="project-stage-update",
    ),
    path(
        "<int:pk>/delete/",
        stage_views.ProjectStageDeleteView.as_view(),
        name="project-stage-delete",
    ),
]
