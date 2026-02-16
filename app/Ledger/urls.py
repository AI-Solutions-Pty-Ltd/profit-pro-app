"""URL configuration for Ledger app."""

from django.urls import path

from app.Ledger.views.chart_views import CreateStandardChartView
from app.Ledger.views.ledger_views import LedgerCreateView, LedgerListView
from app.Ledger.views.report_views import IncomeStatementView
from app.Ledger.views.transaction_views import (
    NonVatRegisteredTransactionCreateView,
    NonVatRegisteredTransactionUpdateView,
    TransactionCreateRouterView,
    TransactionDeleteView,
    TransactionDetailView,
    TransactionListView,
    TransactionUpdateRouterView,
    VatRegisteredTransactionCreateView,
    VatRegisteredTransactionUpdateView,
)

app_name = "ledger"

urlpatterns = [
    # Company-scoped ledger URLs
    path(
        "company/<int:company_id>/ledgers/",
        LedgerListView.as_view(),
        name="ledger-list",
    ),
    path(
        "company/<int:company_id>/ledgers/create/",
        LedgerCreateView.as_view(),
        name="ledger-create",
    ),
    path(
        "company/<int:company_id>/ledgers/create-standard/",
        CreateStandardChartView.as_view(),
        name="create-standard-chart",
    ),
    path(
        "company/<int:company_id>/reports/income-statement/",
        IncomeStatementView.as_view(),
        name="income-statement",
    ),
    # Company-scoped transaction URLs
    path(
        "company/<int:company_id>/transactions/",
        TransactionListView.as_view(),
        name="transaction-list",
    ),
    path(
        "company/<int:company_id>/transactions/create/router/",
        TransactionCreateRouterView.as_view(),
        name="transaction-create",
    ),
    path(
        "company/<int:company_id>/transactions/create/vat/",
        VatRegisteredTransactionCreateView.as_view(),
        name="transaction-create-vat",
    ),
    path(
        "company/<int:company_id>/transactions/create/non-vat/",
        NonVatRegisteredTransactionCreateView.as_view(),
        name="transaction-create-non-vat",
    ),
    # Transaction update URLs
    path(
        "company/<int:company_id>/transactions/<int:pk>/update/router/",
        TransactionUpdateRouterView.as_view(),
        name="transaction-update",
    ),
    path(
        "company/<int:company_id>/transactions/<int:pk>/update/vat/",
        VatRegisteredTransactionUpdateView.as_view(),
        name="transaction-update-vat",
    ),
    path(
        "company/<int:company_id>/transactions/<int:pk>/update/non-vat/",
        NonVatRegisteredTransactionUpdateView.as_view(),
        name="transaction-update-non-vat",
    ),
    path(
        "company/<int:company_id>/transactions/<int:pk>/",
        TransactionDetailView.as_view(),
        name="transaction-detail",
    ),
    path(
        "company/<int:company_id>/transactions/<int:pk>/delete/",
        TransactionDeleteView.as_view(),
        name="transaction-delete",
    ),
]
