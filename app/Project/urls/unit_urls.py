"""URL configuration for Centralized Unit Management."""

from django.urls import path

from ..views import unit_views

urlpatterns = [
    path("units/", unit_views.UnitOfMeasureListView.as_view(), name="unit-list"),
    path(
        "units/create/",
        unit_views.UnitOfMeasureCreateView.as_view(),
        name="unit-create",
    ),
    path(
        "units/<int:pk>/update/",
        unit_views.UnitOfMeasureUpdateView.as_view(),
        name="unit-update",
    ),
    path(
        "units/<int:pk>/delete/",
        unit_views.UnitOfMeasureDeleteView.as_view(),
        name="unit-delete",
    ),
]
