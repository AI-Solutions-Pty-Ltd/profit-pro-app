from django.urls import path

from .views import ClientDetailView, ClientListView, PaymentCertificateFinalApprovalView

app_name = "consultant"

urlpatterns = [
    path("clients/", ClientListView.as_view(), name="client-list"),
    path("client/<int:pk>/", ClientDetailView.as_view(), name="client-detail"),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/approve/",
        PaymentCertificateFinalApprovalView.as_view(),
        name="payment-certificate-approve",
    ),
]
