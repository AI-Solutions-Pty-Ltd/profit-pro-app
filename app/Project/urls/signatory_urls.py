"""URL configuration for Project app."""

from django.urls import path

from app.Project.views import signatory_views

signatory_urls = [
    path(
        "project/<int:project_pk>/signatory_views/",
        signatory_views.SignatoryListView.as_view(),
        name="signatory-list",
    ),
    path(
        "project/<int:project_pk>/signatory_views/create/",
        signatory_views.SignatoryCreateView.as_view(),
        name="signatory-create",
    ),
    path(
        "project/<int:project_pk>/signatory_views/<int:pk>/update/",
        signatory_views.SignatoryUpdateView.as_view(),
        name="signatory-update",
    ),
    path(
        "project/<int:project_pk>/signatory_views/<int:pk>/delete/",
        signatory_views.SignatoryDeleteView.as_view(),
        name="signatory-delete",
    ),
]
