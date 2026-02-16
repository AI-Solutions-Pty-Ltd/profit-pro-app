from django.urls import path

from app.Project.views import project_views

urlpatterns = [
    path(
        "list/",
        project_views.ProjectListView.as_view(),
        name="project-list",
    ),
    path("create/", project_views.ProjectCreateView.as_view(), name="project-create"),
    path(
        "<int:pk>/dashboard/",
        project_views.ProjectDashboardView.as_view(),
        name="project-dashboard",
    ),
    path(
        "<int:pk>/management/",
        project_views.ProjectManagementView.as_view(),
        name="project-management",
    ),
    path(
        "<int:pk>/edit/",
        project_views.ProjectEditView.as_view(),
        name="project-edit",
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
        "<int:pk>/reset-final-account/",
        project_views.ProjectResetFinalAccountView.as_view(),
        name="project-reset-final-account",
    ),
]
