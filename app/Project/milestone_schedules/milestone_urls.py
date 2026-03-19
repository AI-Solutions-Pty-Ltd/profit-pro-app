"""URL configuration for Forecast Hub views."""

from django.urls import path

from app.Project.views import milestone_views

_path_prefix = "milestones/"

urlpatterns = [
    # Milestone CRUD
    path(
        "<int:project_pk>/create/",
        milestone_views.MilestoneCreateView.as_view(),
        name="milestone-create",
    ),
    path(
        "<int:project_pk>/<int:pk>/edit/",
        milestone_views.MilestoneUpdateView.as_view(),
        name="milestone-update",
    ),
    path(
        "<int:project_pk>/<int:pk>/delete/",
        milestone_views.MilestoneDeleteView.as_view(),
        name="milestone-delete",
    ),
    path(
        "<int:project_pk>/<int:pk>/complete/",
        milestone_views.MilestoneCompleteView.as_view(),
        name="milestone-complete",
    ),
]
