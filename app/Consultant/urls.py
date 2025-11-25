from django.urls import path

from .views import (
    ClientDetailView,
    ClientListView,
    PaymentCertificateEditApprovedDateView,
    PaymentCertificateFinalApprovalView,
    PaymentCertificateListView,
)

app_name = "consultant"

urlpatterns = [
    path("clients/", ClientListView.as_view(), name="client-list"),
    path("client/<int:pk>/", ClientDetailView.as_view(), name="client-detail"),
    path(
        "project/<int:project_pk>/payment-certificates/",
        PaymentCertificateListView.as_view(),
        name="payment-certificate-list",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/approve/",
        PaymentCertificateFinalApprovalView.as_view(),
        name="payment-certificate-approve",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/edit-date/",
        PaymentCertificateEditApprovedDateView.as_view(),
        name="payment-certificate-edit-date",
    ),
]
