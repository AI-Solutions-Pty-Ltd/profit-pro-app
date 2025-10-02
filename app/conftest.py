"""Conftest file for pytest."""

import pytest
from django.test import Client

from app.Account.factories import (
    AccountFactory,
    SuburbFactory,
    SuperuserFactory,
    TownFactory,
)
from app.Project.factories import ProjectFactory


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass


@pytest.fixture()
def auth_client(client: Client):
    """Create an authenticated client."""
    user = AccountFactory(email="admin@admin.com", password="password")
    client.force_login(user)
    return client


@pytest.fixture()
def user():
    """Create a basic test user."""
    return AccountFactory(
        email="testuser@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


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
    return ProjectFactory(
        account=user,
        name="Test Project",
    )
