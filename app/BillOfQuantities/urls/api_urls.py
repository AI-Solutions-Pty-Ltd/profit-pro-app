"""URL configuration for Structure app."""

from django.urls import path

from app.BillOfQuantities.views import (
    apis,
)

api_urls = [
    path(
        "project/<int:project_pk>/api/bills/",
        apis.GetBillsByStructureView.as_view(),
        name="api-get-bills",
    ),
    path(
        "project/<int:project_pk>/api/packages/",
        apis.GetPackagesByBillView.as_view(),
        name="api-get-packages",
    ),
]
