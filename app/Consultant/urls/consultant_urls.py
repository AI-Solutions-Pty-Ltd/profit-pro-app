from django.urls import path

from app.Consultant.views import consultant_views

app_name = "consultant"

urlpatterns = [
    path(
        "clients/",
        consultant_views.ClientListView.as_view(),
        name="client-list",
    ),
    path(
        "client/<int:pk>/",
        consultant_views.ClientDetailView.as_view(),
        name="client-detail",
    ),
    path(
        "client/<int:pk>/users/",
        consultant_views.ClientUserListView.as_view(),
        name="client-user-list",
    ),
    path(
        "client/<int:pk>/invite-user/<int:user_pk>/",
        consultant_views.ClientInviteUserView.as_view(),
        name="client-invite-user",
    ),
    path(
        "client/<int:pk>/remove-user/<int:user_pk>/",
        consultant_views.ClientRemoveUserView.as_view(),
        name="client-remove-user",
    ),
    path(
        "resend-invite/<int:pk>/",
        consultant_views.ClientResendInviteView.as_view(),
        name="client-resend-invite",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/",
        consultant_views.PaymentCertificateListView.as_view(),
        name="payment-certificate-list",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/approve/",
        consultant_views.PaymentCertificateFinalApprovalView.as_view(),
        name="payment-certificate-approve",
    ),
    path(
        "project/<int:project_pk>/payment-certificates/<int:pk>/edit-date/",
        consultant_views.PaymentCertificateEditApprovedDateView.as_view(),
        name="payment-certificate-edit-date",
    ),
]
