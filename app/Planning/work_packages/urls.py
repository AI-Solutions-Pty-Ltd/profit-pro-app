"""URL configuration for Planning & Procurement app."""

from django.urls import path

from .views import (
    TenderProcessUpdateView,
    WorkPackageCreateView,
    WorkPackageDeleteView,
    WorkPackageDetailView,
    WorkPackageListView,
    WorkPackageProcessUpdateView,
    WorkPackageUpdateView,
)

_app_name = "planning"
urlpatterns = [
    # Work Packages
    path(
        "<int:project_pk>/work-packages/",
        WorkPackageListView.as_view(),
        name="work-package-list",
    ),
    path(
        "<int:project_pk>/work-packages/create/",
        WorkPackageCreateView.as_view(),
        name="work-package-create",
    ),
    path(
        "<int:project_pk>/work-packages/<int:pk>/",
        WorkPackageDetailView.as_view(),
        name="work-package-detail",
    ),
    path(
        "<int:project_pk>/work-packages/<int:pk>/edit/",
        WorkPackageUpdateView.as_view(),
        name="work-package-update",
    ),
    path(
        "<int:project_pk>/work-packages/<int:pk>/delete/",
        WorkPackageDeleteView.as_view(),
        name="work-package-delete",
    ),
    path(
        "<int:project_pk>/work-packages/<int:pk>/edit-process/",
        WorkPackageProcessUpdateView.as_view(),
        name="work-package-edit-process",
    ),
    path(
        "<int:project_pk>/work-packages/<int:pk>/edit-tender-process/",
        TenderProcessUpdateView.as_view(),
        name="work-package-edit-tender-process",
    ),
]
