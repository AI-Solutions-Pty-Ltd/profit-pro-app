"""URL configuration for Contract Management."""

from django.urls import path

from app.BillOfQuantities.views import contract_views

contract_urls = [
    # Contract Variations
    path(
        "project/<int:project_pk>/variations/",
        contract_views.ContractVariationListView.as_view(),
        name="variation-list",
    ),
    path(
        "project/<int:project_pk>/variations/new/",
        contract_views.ContractVariationCreateView.as_view(),
        name="variation-create",
    ),
    path(
        "project/<int:project_pk>/variations/<int:pk>/",
        contract_views.ContractVariationDetailView.as_view(),
        name="variation-detail",
    ),
    path(
        "project/<int:project_pk>/variations/<int:pk>/edit/",
        contract_views.ContractVariationUpdateView.as_view(),
        name="variation-edit",
    ),
    path(
        "project/<int:project_pk>/variations/<int:pk>/delete/",
        contract_views.ContractVariationDeleteView.as_view(),
        name="variation-delete",
    ),
]
