"""Tests for Account models."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from app.Account.models import Account, Suburb, Town
from app.Account.tests.factories import (
    AccountFactory,
    SuburbFactory,
    SuperuserFactory,
    TownFactory,
)


class TestSuburbModel:
    """Test cases for Suburb model."""

    def test_suburb_creation(self):
        """Test creating a suburb with valid data."""
        suburb = SuburbFactory.create(suburb="Rosebank", postcode="2196")
        assert suburb.pk is not None
        assert suburb.suburb == "Rosebank"
        assert suburb.postcode == "2196"
        assert suburb.created_at is not None
        assert suburb.updated_at is not None

    def test_suburb_str_representation(self):
        """Test the string representation of a suburb."""
        suburb = SuburbFactory.create(suburb="Sandton", postcode="2196")
        assert str(suburb) == "Sandton"

    def test_suburb_unique_constraint(self):
        """Test that suburb name must be unique."""
        SuburbFactory.create(suburb="Sandton", postcode="2196")
        with pytest.raises(IntegrityError):
            Suburb.objects.create(suburb="Sandton", postcode="2000")

    def test_suburb_ordering(self):
        """Test that suburbs are ordered alphabetically."""
        suburb_z = SuburbFactory.create(suburb="Zebra Park", postcode="1234")
        suburb_a = SuburbFactory.create(suburb="Apple Valley", postcode="5678")
        suburb_m = SuburbFactory.create(suburb="Midrand", postcode="9012")

        suburbs = list(Suburb.objects.all())
        assert suburbs[0] == suburb_a
        assert suburbs[1] == suburb_m
        assert suburbs[2] == suburb_z

    def test_suburb_postcode_validation(self):
        """Test postcode validation (must be 4 characters)."""
        # Valid postcode
        suburb = Suburb.objects.create(suburb="Valid Suburb", postcode="1234")
        suburb.full_clean()
        assert suburb.postcode == "1234"

        # Invalid postcode (too short)
        suburb_invalid = Suburb.objects.create(suburb="Invalid Suburb", postcode="123")
        with pytest.raises(ValidationError):
            suburb_invalid.full_clean()

    def test_suburb_postcode_optional(self):
        """Test that postcode is optional."""
        suburb = SuburbFactory.create(suburb="No Postcode Suburb", postcode="")
        assert suburb.postcode == ""

    def test_suburb_soft_delete(self):
        """Test soft delete functionality."""
        suburb = SuburbFactory.create()
        suburb.soft_delete()
        suburb.refresh_from_db()
        assert suburb.deleted is True
        assert suburb.is_deleted is True


class TestTownModel:
    """Test cases for Town model."""

    def test_town_creation(self):
        """Test creating a town with valid data."""
        town = TownFactory.create(town="Pretoria")
        assert town.id is not None
        assert town.town == "Pretoria"
        assert town.created_at is not None
        assert town.updated_at is not None

    def test_town_str_representation(self):
        """Test the string representation of a town."""
        town = TownFactory.create(town="Johannesburg")
        assert str(town) == "Johannesburg"

    def test_town_unique_constraint(self):
        """Test that town name must be unique."""
        TownFactory.create(town="Johannesburg")
        with pytest.raises(IntegrityError):
            Town.objects.create(town="Johannesburg")

    def test_town_ordering(self):
        """Test that towns are ordered alphabetically."""
        town_z = TownFactory.create(town="Zebra Town")
        town_a = TownFactory.create(town="Apple Town")
        town_m = TownFactory.create(town="Midtown")

        towns = list(Town.objects.all())
        assert towns[0] == town_a
        assert towns[1] == town_m
        assert towns[2] == town_z

    def test_town_soft_delete(self):
        """Test soft delete functionality."""
        town = TownFactory.create()
        town.soft_delete()
        town.refresh_from_db()
        assert town.deleted is True
        assert town.is_deleted is True


class TestAccountModel:
    """Test cases for Account model."""

    def test_account_creation_with_email(self):
        """Test creating an account with email."""
        account = AccountFactory.create(
            email="newuser@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )
        assert account.id is not None
        assert account.email == "newuser@example.com"
        assert account.first_name == "John"
        assert account.last_name == "Doe"
        assert account.check_password("password123")
        assert account.is_active is True
        assert account.is_staff is False
        assert account.is_superuser is False

    def test_account_str_representation(self):
        """Test the string representation of an account."""
        account = AccountFactory.create(email="test@example.com")
        assert str(account) == "test@example.com"

    def test_account_email_required(self):
        """Test that email is required."""
        with pytest.raises(ValueError, match="Users require an email field"):
            Account.objects.create_user(
                email="",
                password="password123",
                first_name="Test",
                primary_contact="+27821234567",
            )

    def test_account_email_unique(self):
        """Test that email must be unique."""
        AccountFactory.create(email="test@example.com")
        with pytest.raises(IntegrityError):
            Account.objects.create_user(
                email="test@example.com",
                password="different123",
                first_name="Another",
                primary_contact="+27829999999",
            )

    def test_account_email_normalization(self):
        """Test that email is normalized."""
        account = AccountFactory.create(
            email="Test@EXAMPLE.COM",
            password="password123",
        )
        assert account.email == "Test@example.com"

    def test_create_superuser(self):
        """Test creating a superuser."""
        superuser = SuperuserFactory.create(
            email="admin@example.com",
            password="adminpass123",
            first_name="Admin",
        )
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        assert superuser.check_password("adminpass123")

    def test_create_superuser_validation(self):
        """Test superuser creation validation."""
        with pytest.raises(ValueError, match="Superuser must have is_staff=True"):
            Account.objects.create_superuser(
                email="admin@example.com",
                password="adminpass123",
                first_name="Admin",
                primary_contact="+27821234567",
                is_staff=False,
            )

        with pytest.raises(ValueError, match="Superuser must have is_superuser=True"):
            Account.objects.create_superuser(
                email="admin2@example.com",
                password="adminpass123",
                first_name="Admin",
                primary_contact="+27821234567",
                is_superuser=False,
            )

    def test_account_type_choices(self):
        """Test type field choices."""
        account = AccountFactory.create()
        assert account.type == Account.Type.CLIENT

        account.type = Account.Type.CLIENT
        account.save()
        account.refresh_from_db()
        assert account.type == Account.Type.CLIENT

    def test_account_identification_type_choices(self):
        """Test identification type choices."""
        account = AccountFactory.create()
        assert account.identification_type == Account.IdentificationType.SOUTH_AFRICA_ID

        account.identification_type = Account.IdentificationType.PASSPORT
        account.save()
        account.refresh_from_db()
        assert account.identification_type == Account.IdentificationType.PASSPORT

    def test_account_notification_preferences(self):
        """Test notification preferences."""
        account = AccountFactory.create()
        assert account.notification_preferences == Account.NotificationType.EMAIL

        account.notification_preferences = Account.NotificationType.BOTH
        account.save()
        account.refresh_from_db()
        assert account.notification_preferences == Account.NotificationType.BOTH

    def test_account_phone_numbers(self):
        """Test phone number fields."""
        account = AccountFactory.create(
            email="phone@example.com",
            primary_contact="+27821234567",
            alternative_contact="+27829876543",
        )
        assert str(account.primary_contact) == "082 123 4567"
        assert str(account.alternative_contact) == "082 987 6543"

    def test_account_primary_contact_required(self):
        """Test that primary contact is required."""
        with pytest.raises(IntegrityError):
            account = Account.objects.create_user(
                email="nophone@example.com",
                password="password123",
                first_name="No Phone",
                primary_contact=None,
            )
            account.full_clean()

    def test_account_alternative_contact_optional(self):
        """Test that alternative contact is optional."""
        account = AccountFactory.create(alternative_contact=None)
        assert account.alternative_contact is None or account.alternative_contact == ""

    def test_account_address_field(self):
        """Test address field."""
        account = AccountFactory.create()
        account.address = "123 Main Street, Sandton, 2196"
        account.save()
        account.refresh_from_db()
        assert account.address == "123 Main Street, Sandton, 2196"

    def test_account_identification_number(self):
        """Test identification number field."""
        account = AccountFactory.create()
        account.identification_number = "9001015009087"
        account.save()
        account.refresh_from_db()
        assert account.identification_number == "9001015009087"

    def test_account_soft_delete(self):
        """Test soft delete functionality."""
        account = AccountFactory.create()
        account.soft_delete()
        account.refresh_from_db()
        assert account.deleted is True
        assert account.is_deleted is True

    def test_account_restore(self):
        """Test restore functionality."""
        account = AccountFactory.create()
        account.soft_delete()
        account.refresh_from_db()
        assert account.deleted is True

        account.restore()
        account.refresh_from_db()
        assert account.deleted is False
        assert account.is_deleted is False

    def test_account_username_field(self):
        """Test that username field is email."""
        assert Account.USERNAME_FIELD == "email"
        assert Account.REQUIRED_FIELDS == []

    def test_account_no_username(self):
        """Test that username is not used."""
        account = AccountFactory.create()
        assert account.username is None
