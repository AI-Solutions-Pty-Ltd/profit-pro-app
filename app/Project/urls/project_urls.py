from django.urls import path

from app.Project.views import project_views

project_urls = [
    path("create/", project_views.ProjectCreateView.as_view(), name="project-create"),
    path(
        "<int:pk>/dashboard/",
        project_views.ProjectDashboardView.as_view(),
        name="project-dashboard",
    ),
    path(
        "<int:pk>/",
        project_views.ProjectManagementView.as_view(),
        name="project-management",
    ),
    path(
        "<int:pk>/wbs/",
        project_views.ProjectWBSDetailView.as_view(),
        name="project-wbs-detail",
    ),
    path(
        "<int:pk>/update/",
        project_views.ProjectUpdateView.as_view(),
        name="project-update",
    ),
    path(
        "<int:pk>/delete/",
        project_views.ProjectDeleteView.as_view(),
        name="project-delete",
    ),
]
