"""URL configuration for Project app."""

from django.urls import path

from app.Project import views

app_name = "project"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="project-list"),
    path("create/", views.ProjectCreateView.as_view(), name="project-create"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="project-detail"),
    path("<int:pk>/update/", views.ProjectUpdateView.as_view(), name="project-update"),
    path("<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="project-delete"),
]
