"""Factories for Account models."""

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from app.Account.models import Account, Suburb, Town

User = get_user_model()


class SuburbFactory(DjangoModelFactory[Suburb]):
    """Factory for Suburb model."""

    class Meta:
        model = Suburb
        django_get_or_create = ("suburb",)

    suburb = factory.Sequence(lambda n: f"Suburb {n}")
    postcode = factory.Sequence(lambda n: f"{n:04d}")


class TownFactory(DjangoModelFactory):
    """Factory for Town model."""

    class Meta:
        model = Town
        django_get_or_create = ("town",)

    town = factory.Sequence(lambda n: f"Town {n}")


class AccountFactory(DjangoModelFactory):
    """Factory for Account model."""

    class Meta:
        model = Account
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    primary_contact = factory.Sequence(lambda n: f"+2782{n:07d}")
    alternative_contact = factory.LazyAttribute(
        lambda obj: f"+2783{obj.email.split('@')[0][-7:].zfill(7)}"
        if obj.email
        else None
    )
    ownership = Account.Ownership.PERSONAL
    identification_type = Account.IdentificationType.SOUTH_AFRICA_ID
    identification_number = factory.Faker("numerify", text="##########")
    address = factory.Faker("address")
    notification_preferences = Account.NotificationType.EMAIL
    is_active = True
    is_staff = False
    is_superuser = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default _create to use create_user."""
        password = kwargs.pop("password", "testpass123")
        manager = cls._get_manager(model_class)

        # Use create_user for regular users
        if kwargs.get("is_superuser", False):
            return manager.create_superuser(*args, password=password, **kwargs)
        else:
            return manager.create_user(*args, password=password, **kwargs)


class SuperuserFactory(AccountFactory):
    """Factory for superuser accounts."""

    email = factory.Sequence(lambda n: f"admin{n}@example.com")
    first_name = "Admin"
    last_name = factory.Faker("last_name")
    is_staff = True
    is_superuser = True


class CompanyAccountFactory(AccountFactory):
    """Factory for company accounts."""

    ownership = Account.Ownership.COMPANY
    identification_type = Account.IdentificationType.COMPANY
    identification_number = factory.Faker("numerify", text="####/######/##")


class TenantAccountFactory(AccountFactory):
    """Factory for tenant accounts."""

    ownership = Account.Ownership.TENANT
