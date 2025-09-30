"""Conftest file for pytest."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture()
def auth_client(client: Client):
    user = User.objects.create_user(email="admin@admin.com", password="password")
    client.force_login(user)
    return client
