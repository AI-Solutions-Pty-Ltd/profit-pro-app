"""URL configuration for Project Discipline management."""

from django.urls import path

from app.Project.categories import discipline_views

_prefix = "discipline/"

urlpatterns = [
    path(
        "",
        discipline_views.ProjectDisciplineListView.as_view(),
        name="discipline-list",
    ),
    path(
        "create/",
        discipline_views.ProjectDisciplineCreateView.as_view(),
        name="discipline-create",
    ),
    path(
        "<int:pk>/update/",
        discipline_views.ProjectDisciplineUpdateView.as_view(),
        name="discipline-update",
    ),
    path(
        "<int:pk>/delete/",
        discipline_views.ProjectDisciplineDeleteView.as_view(),
        name="discipline-delete",
    ),
]
