"""Tests for HomeView and the Demo onboarding welcome popup context logic."""

from datetime import timedelta
from typing import cast

import pytest
from django.urls import reverse
from django.utils import timezone

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.Account.tests.factories import AccountFactory
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestHomeViewDemoWelcome:
    """Test cases for the show_demo_welcome_popup context flag in HomeView."""

    def test_anonymous_visitor_welcome_flag(self, client):
        """Test that an anonymous/unauthenticated visitor has the welcome flag set to False."""
        url = reverse("home")
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["show_demo_welcome_popup"] is False

    def test_non_demo_user_welcome_flag(self, client):
        """Test that a regular non-demo user does not see the welcome popup on home page."""
        user = cast(Account, AccountFactory(subscription=Subscription.FREE_TIER))
        client.force_login(user)

        url = reverse("home")
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["show_demo_welcome_popup"] is False

    def test_demo_user_no_projects_welcome_flag(self, client):
        """Test that an active Demo Tier user with no custom projects sees the welcome popup on home page."""
        expiry = timezone.now() + timedelta(days=7)
        user = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=expiry,
            ),
        )
        client.force_login(user)

        url = reverse("home")
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["show_demo_welcome_popup"] is True

    def test_demo_user_with_own_project_welcome_flag(self, client):
        """Test that an active Demo Tier user who has created their own project does not see the welcome popup."""
        expiry = timezone.now() + timedelta(days=7)
        user = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=expiry,
            ),
        )

        # Create a custom project of their own (is_demo=False)
        project = ProjectFactory(is_demo=False)
        project.users.add(user)

        client.force_login(user)

        url = reverse("home")
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["show_demo_welcome_popup"] is False

    def test_demo_user_with_only_demo_projects_welcome_flag(self, client):
        """Test that a demo user with ONLY preloaded/demo projects still sees the welcome popup on home page."""
        expiry = timezone.now() + timedelta(days=7)
        user = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=expiry,
            ),
        )

        # Create a preloaded demo project (is_demo=True)
        ProjectFactory(is_demo=True)

        client.force_login(user)

        url = reverse("home")
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["show_demo_welcome_popup"] is True

    def test_demo_user_no_projects_on_excluded_views(self, client):
        """Test that the welcome popup is suppressed on project creation and profile views, even if user is demo and has no projects."""
        expiry = timezone.now() + timedelta(days=7)
        user = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=expiry,
            ),
        )
        client.force_login(user)

        # Exclusions: 'project:project-create', 'users:account:user_detail', 'users:account:user_edit'
        excluded_urls = [
            reverse("project:project-create"),
            reverse("users:account:user_detail"),
            reverse("users:account:user_edit"),
        ]

        for url in excluded_urls:
            response = client.get(url)
            assert response.status_code == 200
            assert response.context["show_demo_welcome_popup"] is False

    def test_demo_user_no_projects_on_other_regular_page(self, client):
        """Test that the welcome popup shows on other normal pages, like features or about."""
        expiry = timezone.now() + timedelta(days=7)
        user = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=expiry,
            ),
        )
        client.force_login(user)

        # A non-excluded page
        url = reverse("features")
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["show_demo_welcome_popup"] is True
