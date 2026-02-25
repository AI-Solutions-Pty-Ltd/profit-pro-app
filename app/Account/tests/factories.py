"""Factories for Account models."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from factory.declarations import LazyAttribute, Sequence
from factory.django import DjangoModelFactory
from factory.faker import Faker

from app.Account.models import Account, Suburb, Town

User = get_user_model()


class AdminUserFactory(DjangoModelFactory):
    class Meta:
        model = Account

    email = Faker("email")
    password = Faker("password")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    is_staff = True
    is_superuser = True


class UserFactory(AdminUserFactory):
    is_staff = False
    is_superuser = False


class UserGroupFactory(DjangoModelFactory):
    """Factory for UserGroup model."""

    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = Sequence(lambda n: f"Group {n}")


class SuburbFactory(DjangoModelFactory[Suburb]):
    """Factory for Suburb model."""

    class Meta:
        model = Suburb
        django_get_or_create = ("suburb",)

    suburb = Sequence(lambda n: f"Suburb {n}")
    postcode = Sequence(lambda n: f"{n:04d}")


class TownFactory(DjangoModelFactory):
    """Factory for Town model."""

    class Meta:
        model = Town
        django_get_or_create = ("town",)

    town = Sequence(lambda n: f"Town {n}")


class AccountFactory(DjangoModelFactory):
    """Factory for Account model."""

    class Meta:
        model = Account

    email = Faker("email")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    primary_contact = Sequence(lambda n: f"+2782{n:07d}")
    alternative_contact = LazyAttribute(
        lambda obj: (
            f"+2783{obj.email.split('@')[0][-7:].zfill(7)}" if obj.email else None
        )
    )
    type = Account.Type.CLIENT
    identification_type = Account.IdentificationType.SOUTH_AFRICA_ID
    identification_number = Faker("numerify", text="##########")
    address = Faker("address")
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

    email = Faker("email")
    first_name = "Admin"
    last_name = Faker("last_name")
    is_staff = True
    is_superuser = True


class ContractorAccountFactory(AccountFactory):
    """Factory for company accounts."""

    type = Account.Type.CONTRACTOR
    identification_type = Account.IdentificationType.COMPANY
    identification_number = Faker("numerify", text="####/######/##")


class ClientAccountFactory(AccountFactory):
    """Factory for tenant accounts."""

    type = Account.Type.CLIENT
