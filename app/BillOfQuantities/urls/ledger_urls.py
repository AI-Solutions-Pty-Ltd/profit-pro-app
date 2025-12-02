"""URL configuration for Ledger Management."""

from django.urls import path

from app.BillOfQuantities.views import ledger_views

ledger_urls = [
    # Advance Payments
    path(
        "project/<int:project_pk>/advance-payments/",
        ledger_views.AdvancePaymentListView.as_view(),
        name="advance-payment-list",
    ),
    path(
        "project/<int:project_pk>/advance-payments/new/",
        ledger_views.AdvancePaymentCreateView.as_view(),
        name="advance-payment-create",
    ),
    path(
        "project/<int:project_pk>/advance-payments/<int:pk>/edit/",
        ledger_views.AdvancePaymentUpdateView.as_view(),
        name="advance-payment-edit",
    ),
    path(
        "project/<int:project_pk>/advance-payments/<int:pk>/delete/",
        ledger_views.AdvancePaymentDeleteView.as_view(),
        name="advance-payment-delete",
    ),
    # Retention
    path(
        "project/<int:project_pk>/retention/",
        ledger_views.RetentionListView.as_view(),
        name="retention-list",
    ),
    path(
        "project/<int:project_pk>/retention/new/",
        ledger_views.RetentionCreateView.as_view(),
        name="retention-create",
    ),
    path(
        "project/<int:project_pk>/retention/<int:pk>/edit/",
        ledger_views.RetentionUpdateView.as_view(),
        name="retention-edit",
    ),
    path(
        "project/<int:project_pk>/retention/<int:pk>/delete/",
        ledger_views.RetentionDeleteView.as_view(),
        name="retention-delete",
    ),
    # Materials on Site
    path(
        "project/<int:project_pk>/materials-on-site/",
        ledger_views.MaterialsOnSiteListView.as_view(),
        name="materials-list",
    ),
    path(
        "project/<int:project_pk>/materials-on-site/new/",
        ledger_views.MaterialsOnSiteCreateView.as_view(),
        name="materials-create",
    ),
    path(
        "project/<int:project_pk>/materials-on-site/<int:pk>/edit/",
        ledger_views.MaterialsOnSiteUpdateView.as_view(),
        name="materials-edit",
    ),
    path(
        "project/<int:project_pk>/materials-on-site/<int:pk>/delete/",
        ledger_views.MaterialsOnSiteDeleteView.as_view(),
        name="materials-delete",
    ),
    # Escalation
    path(
        "project/<int:project_pk>/escalation/",
        ledger_views.EscalationListView.as_view(),
        name="escalation-list",
    ),
    path(
        "project/<int:project_pk>/escalation/new/",
        ledger_views.EscalationCreateView.as_view(),
        name="escalation-create",
    ),
    path(
        "project/<int:project_pk>/escalation/<int:pk>/edit/",
        ledger_views.EscalationUpdateView.as_view(),
        name="escalation-edit",
    ),
    path(
        "project/<int:project_pk>/escalation/<int:pk>/delete/",
        ledger_views.EscalationDeleteView.as_view(),
        name="escalation-delete",
    ),
    # Special Items (ledger view)
    path(
        "project/<int:project_pk>/special-items-ledger/",
        ledger_views.SpecialItemTransactionListView.as_view(),
        name="special-item-ledger-list",
    ),
]
