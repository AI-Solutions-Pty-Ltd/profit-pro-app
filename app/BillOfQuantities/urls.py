"""URL configuration for Structure app."""

from django.urls import path

from app.BillOfQuantities import views, views_payment_certificate

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
]

urlpatterns = structure_urls + payment_certificate_urls
