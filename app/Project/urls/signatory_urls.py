"""URL configuration for Project app."""

from django.urls import path

from app.Project.views import signatory_views

signatory_urls = [
    path(
        "project/<int:project_pk>/signatories/",
        signatory_views.SignatoryListView.as_view(),
        name="signatory-list",
    ),
    path(
        "project/<int:project_pk>/signatories/invite/",
        signatory_views.SignatoryInviteView.as_view(),
        name="signatory-invite",
    ),
    path(
        "project/<int:project_pk>/signatories/<int:pk>/update/",
        signatory_views.SignatoryUpdateView.as_view(),
        name="signatory-update",
    ),
    path(
        "project/<int:project_pk>/signatories/<int:pk>/delete/",
        signatory_views.SignatoryDeleteView.as_view(),
        name="signatory-delete",
    ),
    path(
        "project/<int:project_pk>/signatories/<int:pk>/resend-invite/",
        signatory_views.SignatoryResendInviteView.as_view(),
        name="signatory-resend-invite",
    ),
    path(
        "project/<int:project_pk>/signatories/link/",
        signatory_views.SignatoryLinkView.as_view(),
        name="signatory-link",
    ),
]
