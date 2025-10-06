"""URL configuration for Structure app."""

from django.urls import path

from app.BillOfQuantities import views

app_name = "structure"

urlpatterns = [
    # Project-scoped structure URLs
    path(
        "project/<int:project_pk>/upload/",
        views.StructureExcelUploadView.as_view(),
        name="structure-upload",
    ),
    path(
        "project/<int:pk>/",
        views.StructureDetailView.as_view(),
        name="structure-detail",
    ),
    path(
        "project/<int:pk>/update/",
        views.StructureUpdateView.as_view(),
        name="structure-update",
    ),
    path(
        "project/<int:pk>/delete/",
        views.StructureDeleteView.as_view(),
        name="structure-delete",
    ),
]
