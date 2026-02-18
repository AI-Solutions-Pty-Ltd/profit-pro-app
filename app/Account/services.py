"""Email verification services."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Account


def send_verification_email(request, user_email: str) -> bool:
    """
    Send verification email to user.

    Args:
        request: The Django request object
        user_email: The email address to send verification to

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        user = Account.objects.get(email=user_email)
    except Account.DoesNotExist:
        messages.error(request, "No account found with this email address.")
        return False

    if user.email_verified:
        messages.info(request, "This email is already verified.")
        return True

    # Generate verification token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Create verification link
    verification_link = request.build_absolute_uri(
        reverse(
            "users:email-verification:verify-email",
            kwargs={"uidb64": uid, "token": token},
        )
    )

    # Send email
    context = {
        "user": user,
        "verification_link": verification_link,
        "site_name": settings.SITE_NAME,
    }

    subject = f"Verify your email address on {settings.SITE_NAME}"
    html_message = render_to_string("auth/email_verification_email.html", context)

    try:
        send_mail(
            subject=subject,
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        messages.success(request, "Verification email sent. Please check your inbox.")
        return True
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        messages.error(request, "Failed to send verification email. Please try again.")
        return False
