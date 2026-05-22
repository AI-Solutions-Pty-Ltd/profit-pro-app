"""Management command to create a demo user account."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from app.Account.models import Account
from app.Account.subscription_config import Subscription


class Command(BaseCommand):
    """Creates or updates a demo user account with standard demo tier."""

    help = "Creates or updates a demo user account with standard demo tier and active subscription"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            default="demo@example.com",
            help="Email address of the demo user",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="DemoPass123!",
            help="Password of the demo user",
        )
        parser.add_argument(
            "--first-name",
            type=str,
            default="Demo",
            help="First name of the demo user",
        )
        parser.add_argument(
            "--last-name",
            type=str,
            default="User",
            help="Last name of the demo user",
        )
        parser.add_argument(
            "--phone",
            type=str,
            default="+27821234567",
            help="Primary contact number of the demo user",
        )

    def handle(self, *args, **options):
        email = options["email"].lower().strip()
        password = options["password"]
        first_name = options["first_name"]
        last_name = options["last_name"]
        phone = options["phone"]

        # Check if user already exists
        if Account.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Account with email '{email}' already exists. Updating existing user to active Demo Tier."
                )
            )
            user = Account.objects.get(email=email)
            user.subscription = Subscription.DEMO_TIER
            user.subscription_expires_at = timezone.now() + timedelta(days=7)
            user.first_name = first_name
            user.last_name = last_name
            user.primary_contact = phone
            user.set_password(password)
            user.is_active = True
            user.save()
        else:
            user = Account.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                primary_contact=phone,
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=timezone.now() + timedelta(days=7),
            )
            self.stdout.write(
                self.style.SUCCESS("Successfully created a new demo user.")
            )

        # Seed and verify demo companies
        from app.Project.models import Company

        Company.ensure_demo_companies()
        self.stdout.write(
            self.style.SUCCESS("Successfully seeded or verified demo companies.")
        )

        self.stdout.write(self.style.SUCCESS(f"Email:        {user.email}"))
        self.stdout.write(self.style.SUCCESS(f"Password:     {password}"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Subscription: {user.get_subscription_display()} (expires at: {user.subscription_expires_at})"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Status:       Active (time left: {user.demo_time_left_str})"
            )
        )
