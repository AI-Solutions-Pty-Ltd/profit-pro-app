"""URL configuration for Structure app."""

from django.urls import path

from app.BillOfQuantities.views import (
    structure_views,
)

structure_urls = [
    # Project-scoped structure URLs
    path(
        "project/<int:project_pk>/wbs/upload/",
        structure_views.StructureExcelUploadView.as_view(),
        name="structure-upload",
    ),
    path(
        "project/<int:project_pk>/structures/",
        structure_views.StructureListView.as_view(),
        name="structure-list",
    ),
    path(
        "project/<int:project_pk>/structure/<int:pk>/",
        structure_views.StructureDetailView.as_view(),
        name="structure-detail",
    ),
    path(
        "project/<int:project_pk>/structure/<int:pk>/update/",
        structure_views.StructureUpdateView.as_view(),
        name="structure-update",
    ),
    path(
        "project/<int:project_pk>/structure/<int:pk>/delete/",
        structure_views.StructureDeleteView.as_view(),
        name="structure-delete",
    ),
]
