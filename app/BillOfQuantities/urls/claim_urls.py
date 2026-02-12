"""URLs for Claim views."""

from django.urls import path

from app.BillOfQuantities.views.claim_views import (
    ClaimCreateView,
    ClaimDeleteView,
    ClaimListView,
    ClaimUpdateView,
)

app_name = "claims"

urlpatterns = [
    path(
        "<int:project_pk>/claims/",
        ClaimListView.as_view(),
        name="claim-list",
    ),
    path(
        "<int:project_pk>/claims/create/",
        ClaimCreateView.as_view(),
        name="claim-create",
    ),
    path(
        "<int:project_pk>/claims/<int:pk>/update/",
        ClaimUpdateView.as_view(),
        name="claim-update",
    ),
    path(
        "<int:project_pk>/claims/<int:pk>/delete/",
        ClaimDeleteView.as_view(),
        name="claim-delete",
    ),
]

# Create the claim_urls variable for import
claim_urls = urlpatterns
