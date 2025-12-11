"""URL patterns for Compliance Management."""

from django.urls import path

from app.Project.views.compliance_views import (
    AdministrativeComplianceCreateView,
    AdministrativeComplianceDeleteView,
    AdministrativeComplianceListView,
    AdministrativeComplianceUpdateView,
    ComplianceDashboardView,
    ContractualComplianceCreateView,
    ContractualComplianceDeleteView,
    ContractualComplianceListView,
    ContractualComplianceUpdateView,
    FinalAccountComplianceCreateView,
    FinalAccountComplianceDeleteView,
    FinalAccountComplianceListView,
    FinalAccountComplianceUpdateView,
)

urlpatterns = [
    # Dashboard
    path(
        "<int:project_pk>/compliance/",
        ComplianceDashboardView.as_view(),
        name="compliance-dashboard",
    ),
    # Contractual Compliance
    path(
        "<int:project_pk>/compliance/contractual/",
        ContractualComplianceListView.as_view(),
        name="contractual-compliance-list",
    ),
    path(
        "<int:project_pk>/compliance/contractual/create/",
        ContractualComplianceCreateView.as_view(),
        name="contractual-compliance-create",
    ),
    path(
        "<int:project_pk>/compliance/contractual/<int:pk>/edit/",
        ContractualComplianceUpdateView.as_view(),
        name="contractual-compliance-update",
    ),
    path(
        "<int:project_pk>/compliance/contractual/<int:pk>/delete/",
        ContractualComplianceDeleteView.as_view(),
        name="contractual-compliance-delete",
    ),
    # Administrative Compliance
    path(
        "<int:project_pk>/compliance/administrative/",
        AdministrativeComplianceListView.as_view(),
        name="administrative-compliance-list",
    ),
    path(
        "<int:project_pk>/compliance/administrative/create/",
        AdministrativeComplianceCreateView.as_view(),
        name="administrative-compliance-create",
    ),
    path(
        "<int:project_pk>/compliance/administrative/<int:pk>/edit/",
        AdministrativeComplianceUpdateView.as_view(),
        name="administrative-compliance-update",
    ),
    path(
        "<int:project_pk>/compliance/administrative/<int:pk>/delete/",
        AdministrativeComplianceDeleteView.as_view(),
        name="administrative-compliance-delete",
    ),
    # Final Account Compliance
    path(
        "<int:project_pk>/compliance/final-account/",
        FinalAccountComplianceListView.as_view(),
        name="final-account-compliance-list",
    ),
    path(
        "<int:project_pk>/compliance/final-account/create/",
        FinalAccountComplianceCreateView.as_view(),
        name="final-account-compliance-create",
    ),
    path(
        "<int:project_pk>/compliance/final-account/<int:pk>/edit/",
        FinalAccountComplianceUpdateView.as_view(),
        name="final-account-compliance-update",
    ),
    path(
        "<int:project_pk>/compliance/final-account/<int:pk>/delete/",
        FinalAccountComplianceDeleteView.as_view(),
        name="final-account-compliance-delete",
    ),
]
