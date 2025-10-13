"""URL configuration for Project app."""

from django.urls import path

from app.Project import views, views_clients

app_name = "project"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="project-list"),
    path("create/", views.ProjectCreateView.as_view(), name="project-create"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="project-detail"),
    path(
        "<int:pk>/wbs/", views.ProjectWBSDetailView.as_view(), name="project-wbs-detail"
    ),
    path("<int:pk>/update/", views.ProjectUpdateView.as_view(), name="project-update"),
    path("<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="project-delete"),
    path(
        "<int:project_pk>/add-client/",
        views_clients.ProjectAddClientView.as_view(),
        name="project-add-client",
    ),
    path(
        "<int:project_pk>/edit-client/<int:pk>/",
        views_clients.ProjectEditClientView.as_view(),
        name="project-edit-client",
    ),
    path(
        "client/<int:client_pk>/invite-user/",
        views_clients.ClientInviteUserView.as_view(),
        name="client-invite-user",
    ),
    path(
        "client/<int:client_pk>/resend-invite/",
        views_clients.ClientResendInviteView.as_view(),
        name="client-resend-invite",
    ),
    path(
        "client/<int:client_pk>/remove-user/",
        views_clients.ClientRemoveUserView.as_view(),
        name="client-remove-user",
    ),
]
