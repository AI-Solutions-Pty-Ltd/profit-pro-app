from factory.django import DjangoModelFactory
from factory import Faker
from Account.models import Account


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
