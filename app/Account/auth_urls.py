# The views used below are normally mapped in the AdminSite instance.
# This URLs file is used to provide a reliable view deployment for test purposes.
# It is also provided as a convenience to those who want to deploy these URLs
# elsewhere.

from django.contrib.auth import views
from django.urls import path

urlpatterns = [
    path(
        "login/",
        views.LoginView.as_view(template_name="auth/login.html", next_page="home"),
        name="login",
    ),
    path("logout/", views.LogoutView.as_view(next_page="home"), name="logout"),
    path(
        "password_change/",
        views.PasswordChangeView.as_view(
            template_name="auth/password_change_form.html",
            success_url="/password_change/done/",
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        views.PasswordChangeDoneView.as_view(
            template_name="auth/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path(
        "password_reset/",
        views.PasswordResetView.as_view(
            template_name="auth/password_reset_form.html",
            subject_template_name="auth/password_reset_subject.txt",
            email_template_name="auth/password_reset_email.html",
            html_email_template_name="auth/password_reset_email.html",
            success_url="/password_reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html", success_url="/reset/done/"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
