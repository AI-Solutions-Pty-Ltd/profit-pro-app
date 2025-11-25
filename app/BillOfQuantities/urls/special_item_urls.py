"""URL configuration for Structure app."""

from django.urls import path

from app.BillOfQuantities.views import (
    special_item_views,
)

special_item_urls = [
    path(
        "project/<int:project_pk>/special-items/",
        special_item_views.SpecialItemListView.as_view(),
        name="special-item-list",
    ),
    path(
        "project/<int:project_pk>/special-items/create/",
        special_item_views.SpecialItemCreateView.as_view(),
        name="special-item-create",
    ),
    path(
        "project/<int:project_pk>/special-items/<int:pk>/update/",
        special_item_views.SpecialItemUpdateView.as_view(),
        name="special-item-update",
    ),
    path(
        "project/<int:project_pk>/special-items/<int:pk>/delete/",
        special_item_views.SpecialItemDeleteView.as_view(),
        name="special-item-delete",
    ),
]
