import pytest

from app.Account.tests.factories import UserFactory, UserGroupFactory


@pytest.fixture
def consultant_user_group():
    return UserGroupFactory.create(name="consultant")


@pytest.fixture
def consultant_user(consultant_user_group):
    user = UserFactory.create()
    user.groups.add(consultant_user_group)
    return user
