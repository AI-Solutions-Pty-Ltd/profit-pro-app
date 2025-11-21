from django.urls import path

import app.Inventories.views_suppliers

app_name = "suppliers"

urlpatterns = [
    path(
        "create/",
        app.Inventories.views_suppliers.SupplierCreateView.as_view(),
        name="supplier_create_view",
    ),
    path(
        "list/",
        app.Inventories.views_suppliers.SupplierListView.as_view(),
        name="supplier_list_view",
    ),
    path(
        "detail/<int:supplier>/",
        app.Inventories.views_suppliers.SupplierDetailView.as_view(),
        name="supplier_detail_view",
    ),
    path(
        "statement/<int:supplier>/",
        app.Inventories.views_suppliers.SupplierStatementView.as_view(),
        name="supplier_statement_view",
    ),
    path(
        "invoice/<int:invoice>/",
        app.Inventories.views_suppliers.SupplierInvoiceFileServeView.as_view(),
        name="supplier_invoice_view",
    ),
]
