"""URL patterns for Compliance Management."""

from django.urls import path

from app.Project.views import compliance_views

_path_prefix = "compliance/"

urlpatterns = [
    # Dashboard
    path(
        "<int:project_pk>/",
        compliance_views.ComplianceDashboardView.as_view(),
        name="compliance-dashboard",
    ),
    # Contractual Compliance
    path(
        "<int:project_pk>/contractual/",
        compliance_views.ContractualComplianceListView.as_view(),
        name="contractual-compliance-list",
    ),
    path(
        "<int:project_pk>/contractual/create/",
        compliance_views.ContractualComplianceCreateView.as_view(),
        name="contractual-compliance-create",
    ),
    path(
        "<int:project_pk>/contractual/<int:pk>/",
        compliance_views.ContractualComplianceDetailView.as_view(),
        name="contractual-compliance-detail",
    ),
    path(
        "<int:project_pk>/contractual/<int:pk>/edit/",
        compliance_views.ContractualComplianceUpdateView.as_view(),
        name="contractual-compliance-update",
    ),
    path(
        "<int:project_pk>/contractual/<int:pk>/delete/",
        compliance_views.ContractualComplianceDeleteView.as_view(),
        name="contractual-compliance-delete",
    ),
    path(
        "<int:project_pk>/contractual/<int:pk>/dialog/",
        compliance_views.ContractualComplianceDialogView.as_view(),
        name="contractual-compliance-dialog",
    ),
    # Administrative Compliance
    path(
        "<int:project_pk>/administrative/",
        compliance_views.AdministrativeComplianceListView.as_view(),
        name="administrative-compliance-list",
    ),
    path(
        "<int:project_pk>/administrative/create/",
        compliance_views.AdministrativeComplianceCreateView.as_view(),
        name="administrative-compliance-create",
    ),
    path(
        "<int:project_pk>/administrative/<int:pk>/",
        compliance_views.AdministrativeComplianceDetailView.as_view(),
        name="administrative-compliance-detail",
    ),
    path(
        "<int:project_pk>/administrative/<int:pk>/edit/",
        compliance_views.AdministrativeComplianceUpdateView.as_view(),
        name="administrative-compliance-update",
    ),
    path(
        "<int:project_pk>/administrative/<int:pk>/delete/",
        compliance_views.AdministrativeComplianceDeleteView.as_view(),
        name="administrative-compliance-delete",
    ),
    path(
        "<int:project_pk>/administrative/<int:pk>/dialog/",
        compliance_views.AdministrativeComplianceDialogView.as_view(),
        name="administrative-compliance-dialog",
    ),
    # Final Account Compliance
    path(
        "<int:project_pk>/final-account/",
        compliance_views.FinalAccountComplianceListView.as_view(),
        name="final-account-compliance-list",
    ),
    path(
        "<int:project_pk>/final-account/create/",
        compliance_views.FinalAccountComplianceCreateView.as_view(),
        name="final-account-compliance-create",
    ),
    path(
        "<int:project_pk>/final-account/<int:pk>/",
        compliance_views.FinalAccountComplianceDetailView.as_view(),
        name="final-account-compliance-detail",
    ),
    path(
        "<int:project_pk>/final-account/<int:pk>/edit/",
        compliance_views.FinalAccountComplianceUpdateView.as_view(),
        name="final-account-compliance-update",
    ),
    path(
        "<int:project_pk>/final-account/<int:pk>/delete/",
        compliance_views.FinalAccountComplianceDeleteView.as_view(),
        name="final-account-compliance-delete",
    ),
    path(
        "<int:project_pk>/final-account/<int:pk>/dialog/",
        compliance_views.FinalAccountComplianceDialogView.as_view(),
        name="final-account-compliance-dialog",
    ),
]
