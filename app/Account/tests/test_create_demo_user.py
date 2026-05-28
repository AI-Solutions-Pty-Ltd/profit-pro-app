"""Tests for the create_demo_user management command."""

import pytest
from django.core.management import call_command

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.Account.tests.factories import AccountFactory


@pytest.mark.django_db
class TestCreateDemoUserCommand:
    """Test cases for the create_demo_user management command."""

    def test_create_demo_user_defaults(self):
        """Test creating a demo user with default options."""
        email = "demo@example.com"

        # Verify user does not exist yet
        assert not Account.objects.filter(email=email).exists()

        # Run command
        call_command("create_demo_user")

        # Verify user exists and has correct attributes
        assert Account.objects.filter(email=email).exists()
        user = Account.objects.get(email=email)
        assert user.email == email
        assert user.first_name == "Demo"
        assert user.last_name == "User"
        assert str(user.primary_contact) == "082 123 4567"
        assert user.subscription == Subscription.DEMO_TIER
        assert user.subscription_expires_at is not None
        assert user.has_demo_permission is True
        assert user.is_active is True
        assert user.check_password("DemoPass123!") is True

    def test_create_demo_user_custom_arguments(self):
        """Test creating a demo user with custom options."""
        email = "custom_demo@example.com"
        password = "CustomPassword789!"
        first_name = "Jane"
        last_name = "Doe"
        phone = "+27831112222"

        # Verify user does not exist yet
        assert not Account.objects.filter(email=email).exists()

        # Run command with options
        call_command(
            "create_demo_user",
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )

        # Verify user exists and has custom attributes
        assert Account.objects.filter(email=email).exists()
        user = Account.objects.get(email=email)
        assert user.email == email
        assert user.first_name == first_name
        assert user.last_name == last_name
        assert str(user.primary_contact) == "083 111 2222"
        assert user.subscription == Subscription.DEMO_TIER
        assert user.subscription_expires_at is not None
        assert user.has_demo_permission is True
        assert user.is_active is True
        assert user.check_password(password) is True

    def test_update_existing_user_to_demo(self):
        """Test that running the command on an existing user updates them to active demo tier."""
        # Create a user who is not a demo user and is on another subscription level
        existing_user = AccountFactory(
            email="existing@example.com",
            subscription=Subscription.BUSINESS_MANAGEMENT,
            subscription_expires_at=None,
        )
        existing_user.set_password("OldPass123!")
        existing_user.save()

        assert existing_user.subscription == Subscription.BUSINESS_MANAGEMENT
        assert existing_user.has_demo_permission is False

        # Run command with same email
        call_command(
            "create_demo_user",
            email="existing@example.com",
            password="NewDemoPass123!",
            first_name="Updated",
            last_name="User",
            phone="+27845556666",
        )

        # Refresh from db
        existing_user.refresh_from_db()

        # Verify attributes were updated
        assert existing_user.first_name == "Updated"
        assert existing_user.last_name == "User"
        assert str(existing_user.primary_contact) == "084 555 6666"
        assert existing_user.subscription == Subscription.DEMO_TIER
        assert existing_user.subscription_expires_at is not None
        assert existing_user.has_demo_permission is True
        assert existing_user.check_password("NewDemoPass123!") is True
