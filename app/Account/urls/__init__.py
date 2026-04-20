"""Main URL configuration for Account app."""

from django.urls import include, path

app_name = "users"
_path_prefix = "users/"  # reference only

urlpatterns = [
    path("auth/", include("app.Account.urls.auth_urls", "auth")),
    path("account/", include("app.Account.urls.account_urls", "account")),
    path(
        "email-verification/",
        include("app.Account.urls.email_verification_urls", "email-verification"),
    ),
]
