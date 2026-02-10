"""Tasks for Project app."""

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from app.Account.models import Account


def send_project_user_welcome_email(
    user: Account,
    project_name: str,
    request_domain: str,
    request_protocol: str = "http",
) -> bool:
    """
    Send a welcome email to a newly created project user with password setup instructions.

    Args:
        user: The Account object for the new user
        project_name: Name of the project the user was added to
        request_domain: The domain from the request (e.g., 'example.com')
        request_protocol: Protocol from request ('http' or 'https')

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not settings.USE_EMAIL:
        return False

    try:
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        context = {
            "user": user,
            "protocol": request_protocol,
            "domain": request_domain,
            "uid": uid,
            "token": token,
            "site_name": settings.SITE_NAME,
            "project_name": project_name,
            "expiry_hours": 24,
        }

        subject = f"You've been invited to join {project_name} on {settings.SITE_NAME}"
        html_message = render_to_string(
            "portfolio/emails/project_user_welcome.html", context
        )

        send_mail(
            subject=subject,
            message="",  # Plain text version (optional)
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return True

    except Exception as e:
        # Log the error in production
        print(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False
