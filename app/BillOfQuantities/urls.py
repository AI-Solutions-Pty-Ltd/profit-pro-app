"""URL configuration for Structure app."""

from django.urls import path

from app.BillOfQuantities import (
    views,
    views_addendum,
    views_api,
    views_forecast,
    views_payment_certificate,
    views_special_item,
)

app_name = "bill_of_quantities"

structure_urls = [
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

payment_certificate_urls = [
    path(
        "project/<int:project_pk>/payment-certificates/",
        views_payment_certificate.PaymentCertificateListView.as_view(),
        name="payment-certificate-list",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/detail/",
        views_payment_certificate.PaymentCertificateDetailView.as_view(),
        name="payment-certificate-detail",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/new/",
        views_payment_certificate.PaymentCertificateEditView.as_view(),
        name="payment-certificate-new",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/edit/",
        views_payment_certificate.PaymentCertificateEditView.as_view(),
        name="payment-certificate-edit",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/submit/",
        views_payment_certificate.PaymentCertificateSubmitView.as_view(),
        name="payment-certificate-submit",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/download-pdf/",
        views_payment_certificate.PaymentCertificateDownloadPDFView.as_view(),
        name="payment-certificate-download-pdf",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/download-abridged-pdf/",
        views_payment_certificate.PaymentCertificateDownloadAbridgedPDFView.as_view(),
        name="payment-certificate-download-abridged-pdf",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/pdf-status/",
        views_payment_certificate.PaymentCertificatePDFStatusView.as_view(),
        name="payment-certificate-pdf-status",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/email/",
        views_payment_certificate.PaymentCertificateEmailView.as_view(),
        name="payment-certificate-email",
    ),
]

addendum_urls = [
    path(
        "project/<int:project_pk>/addendum/",
        views_addendum.AddendumListView.as_view(),
        name="addendum-list",
    ),
    path(
        "project/<int:project_pk>/addendum/create/",
        views_addendum.AddendumCreateView.as_view(),
        name="addendum-create",
    ),
    path(
        "project/<int:project_pk>/addendum/<int:pk>/update/",
        views_addendum.AddendumUpdateView.as_view(),
        name="addendum-update",
    ),
    path(
        "project/<int:project_pk>/addendum/<int:pk>/delete/",
        views_addendum.AddendumDeleteView.as_view(),
        name="addendum-delete",
    ),
]

special_item_urls = [
    path(
        "project/<int:project_pk>/special-items/",
        views_special_item.SpecialItemListView.as_view(),
        name="special-item-list",
    ),
    path(
        "project/<int:project_pk>/special-items/create/",
        views_special_item.SpecialItemCreateView.as_view(),
        name="special-item-create",
    ),
    path(
        "project/<int:project_pk>/special-items/<int:pk>/update/",
        views_special_item.SpecialItemUpdateView.as_view(),
        name="special-item-update",
    ),
    path(
        "project/<int:project_pk>/special-items/<int:pk>/delete/",
        views_special_item.SpecialItemDeleteView.as_view(),
        name="special-item-delete",
    ),
]

forecast_urls = [
    path(
        "project/<int:project_pk>/forecasts/",
        views_forecast.ForecastListView.as_view(),
        name="forecast-list",
    ),
    path(
        "project/<int:project_pk>/forecasts/create/",
        views_forecast.ForecastCreateView.as_view(),
        name="forecast-create",
    ),
    path(
        "project/<int:project_pk>/forecasts/<int:pk>/edit/",
        views_forecast.ForecastEditView.as_view(),
        name="forecast-edit",
    ),
    path(
        "project/<int:project_pk>/forecasts/<int:pk>/approve/",
        views_forecast.ForecastApproveView.as_view(),
        name="forecast-approve",
    ),
    path(
        "project/<int:project_pk>/forecasts/report/",
        views_forecast.ForecastReportView.as_view(),
        name="forecast-report",
    ),
]

api_urls = [
    path(
        "project/<int:project_pk>/api/bills/",
        views_api.GetBillsByStructureView.as_view(),
        name="api-get-bills",
    ),
    path(
        "project/<int:project_pk>/api/packages/",
        views_api.GetPackagesByBillView.as_view(),
        name="api-get-packages",
    ),
]

urlpatterns = (
    structure_urls
    + payment_certificate_urls
    + addendum_urls
    + special_item_urls
    + forecast_urls
    + api_urls
)
