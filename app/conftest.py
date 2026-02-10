"""Conftest file for pytest."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from app.Account.models import Account
from app.Account.tests.factories import (
    AccountFactory,
    SuburbFactory,
    SuperuserFactory,
    TownFactory,
)
from app.BillOfQuantities.tests.factories import LineItemFactory
from app.Project.tests.factories import ProjectFactory

User = get_user_model()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass


@pytest.fixture()
def auth_client(client: Client):
    """Create an authenticated client."""
    user = AccountFactory(email="admin@admin.com", password="password")
    # AccountFactory returns an Account instance, not a factory object
    client.force_login(user)  # type: ignore[arg-type]
    return client


@pytest.fixture()
def user() -> Account:
    """Create a basic test user."""

    user: Account = AccountFactory.create(
        email="testuser@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )
    return user


@pytest.fixture()
def superuser():
    """Create a superuser for testing."""
    return SuperuserFactory(
        email="superuser@example.com",
        password="superpass123",
        first_name="Super",
        last_name="User",
    )


@pytest.fixture()
def suburb():
    """Create a test suburb."""
    return SuburbFactory(suburb="Test Suburb", postcode="1234")


@pytest.fixture()
def town():
    """Create a test town."""
    return TownFactory(town="Test Town")


@pytest.fixture()
def project(user):
    """Create a test project."""
    project = ProjectFactory.create(name="Test Project", users=(user,))
    LineItemFactory.create(project=project)
    return project
