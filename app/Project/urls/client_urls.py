"""URL configuration for Project app."""

from django.urls import path

from app.Project.views import client_views

client_urls = [
    path(
        "project/<int:project_pk>/add-client/",
        client_views.ProjectAddClientView.as_view(),
        name="project-add-client",
    ),
    path(
        "project/<int:project_pk>/edit-client/<int:pk>/",
        client_views.ClientEditView.as_view(),
        name="client-edit",
    ),
    path(
        "project/<int:project_pk>/client/<int:pk>/invite-user/",
        client_views.ClientInviteUserView.as_view(),
        name="client-invite-user",
    ),
    path(
        "project/<int:project_pk>/client/<int:pk>/resend-invite/",
        client_views.ClientResendInviteView.as_view(),
        name="client-resend-invite",
    ),
    path(
        "project/<int:project_pk>/client/<int:pk>/remove-user/",
        client_views.ClientRemoveUserView.as_view(),
        name="client-remove-user",
    ),
    path(
        "project/<int:project_pk>/client/<int:pk>/remove/",
        client_views.ClientRemoveView.as_view(),
        name="client-remove",
    ),
]
