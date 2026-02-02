"""URL configuration for Structure app."""

from django.urls import path

from app.BillOfQuantities.views import (
    payment_certificate_payment_views,
)

payment_certificate_payment_urls = [
    path(
        "project/<int:project_pk>/payment-certificates/payment-statement/",
        payment_certificate_payment_views.PaymentCertificatePaymentStatementView.as_view(),
        name="payment-certificate-payment-statement",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/email-statement/",
        payment_certificate_payment_views.EmailPaymentStatementView.as_view(),
        name="email-payment-statement",
    ),
    # Payment CRUD URLs
    path(
        "project/<int:project_pk>/payment-certificates/payments/new/",
        payment_certificate_payment_views.CreatePaymentCertificatePaymentView.as_view(),
        name="create-payment-certificate-payment",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/payments/<int:pk>/edit/",
        payment_certificate_payment_views.UpdatePaymentCertificatePaymentView.as_view(),
        name="update-payment-certificate-payment",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/payments/<int:pk>/delete/",
        payment_certificate_payment_views.DeletePaymentCertificatePaymentView.as_view(),
        name="delete-payment-certificate-payment",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/invoice/",
        payment_certificate_payment_views.PaymentCertificateInvoiceView.as_view(),
        name="payment-certificate-invoice",
    ),
]
