"""URL configuration for Forecast Hub views."""

from django.urls import path

from app.Project.views import milestone_views

urlpatterns = [
    # Milestone CRUD
    path(
        "project/<int:project_pk>/milestones/create/",
        milestone_views.MilestoneCreateView.as_view(),
        name="milestone-create",
    ),
    path(
        "project/<int:project_pk>/milestones/<int:pk>/edit/",
        milestone_views.MilestoneUpdateView.as_view(),
        name="milestone-update",
    ),
    path(
        "project/<int:project_pk>/milestones/<int:pk>/delete/",
        milestone_views.MilestoneDeleteView.as_view(),
        name="milestone-delete",
    ),
    path(
        "project/<int:project_pk>/milestones/<int:pk>/complete/",
        milestone_views.MilestoneCompleteView.as_view(),
        name="milestone-complete",
    ),
]
