"""Email verification views for Account app."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.views.generic import View

from app.Account.models import Account
from app.Account.services import send_verification_email


class SendVerificationEmailView(View):
    """Send verification email to user."""

    def get(self, request, user_email, *args, **kwargs):
        """Handle GET request to send verification email."""
        send_verification_email(request, user_email)
        return redirect("home")


class VerifyEmailView(View):
    """Verify email using token."""

    def get(self, request, uidb64, token, *args, **kwargs):
        """Handle GET request to verify email."""
        try:
            # Decode the user ID
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Account.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
            user = None

        # Check if the token is valid
        if user is not None and default_token_generator.check_token(user, token):
            # Mark email as verified
            user.email_verified = True
            user.email_verified_at = timezone.now()
            user.save()

            # Send thank you email
            try:
                context = {
                    "user": user,
                    "site_name": settings.SITE_NAME,
                }
                subject = f"Welcome to {settings.SITE_NAME}!"
                html_message = render_to_string(
                    "auth/email_verification_thank_you.html", context
                )

                send_mail(
                    subject=subject,
                    message="",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception:
                # Log error but don't fail the verification process
                pass

            messages.success(request, "Your email has been verified successfully!")
            # Log the user in
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "The verification link is invalid or has expired.")
            return redirect("users:auth:login")
