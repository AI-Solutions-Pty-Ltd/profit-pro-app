from django.conf import settings

from Account.models import Account
from app.core.Utilities.django_email_service import django_email_service


def send_welcome_email(account: Account):
    print("Sending welcome email to", account.email)
    if account.email:
        subject = f"Welcome to {settings.SITE_NAME}"
        html_body = f"""
            <h3 style="font-weight: lighter !important;">Thank you for registering with {settings.SITE_NAME}. </h3>
            <h3 style="font-weight: lighter !important;">Profile Information<h3>
            <ul style="font-weight: lighter !important;">
                <li style="font-weight: lighter !important;">First Name: {account.first_name}</li>
                <li style="font-weight: lighter !important;">Last Name: {account.last_name}</li>
                <li style="font-weight: lighter !important;">Email: {account.email}</li>
                <li style="font-weight: lighter !important;">Phone: {account.primary_contact}</li>
            </ul>
            <p style="font-weight: lighter !important;">Regards</p>
            <h3 style="font-weight: lighter !important;">The {settings.SITE_NAME} Team</h3>
        """
        django_email_service(
            to=account.email,
            subject=subject,
            html_body=html_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
        )
        print("Email sent to", account.email)
    else:
        print("No email address found for account", account.pk)
