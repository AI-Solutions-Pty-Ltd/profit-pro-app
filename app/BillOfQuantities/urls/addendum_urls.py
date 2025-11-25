"""URL configuration for Structure app."""

from django.urls import path

from app.BillOfQuantities.views import (
    addendum_views,
)

addendum_urls = [
    path(
        "project/<int:project_pk>/addendum/",
        addendum_views.AddendumListView.as_view(),
        name="addendum-list",
    ),
    path(
        "project/<int:project_pk>/addendum/create/",
        addendum_views.AddendumCreateView.as_view(),
        name="addendum-create",
    ),
    path(
        "project/<int:project_pk>/addendum/<int:pk>/update/",
        addendum_views.AddendumUpdateView.as_view(),
        name="addendum-update",
    ),
    path(
        "project/<int:project_pk>/addendum/<int:pk>/delete/",
        addendum_views.AddendumDeleteView.as_view(),
        name="addendum-delete",
    ),
]
