"""URL patterns for email verification."""

from django.urls import path

from app.Account.views.email_verification_views import (
    SendVerificationEmailView,
    VerifyEmailView,
)

_app_prefix = "users"  # reference only
_path_prefix = "users/email-verification/"  # reference only

app_name = "email-verification"


urlpatterns = [
    path(
        "send-verification/<user_email>/",
        SendVerificationEmailView.as_view(),
        name="send-verification-email",
    ),
    path(
        "verify-email/<uidb64>/<token>/",
        VerifyEmailView.as_view(),
        name="verify-email",
    ),
]
