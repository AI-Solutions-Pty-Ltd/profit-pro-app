"""Tests for the Demo Tier and subscription expiration logic."""

from datetime import timedelta
from typing import cast

import pytest
from django.utils import timezone

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.Account.tests.factories import AccountFactory


@pytest.mark.django_db
class TestDemoTier:
    """Test cases for Demo Tier behavior."""

    def test_demo_tier_access_before_expiry(self):
        """Test that Demo Tier grants access before expiration."""
        expiry = timezone.now() + timedelta(days=7)
        user: Account = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=expiry,
            ),
        )

        # Should have access to business management (parent of demo)
        assert user.has_subscription_tier([Subscription.BUSINESS_MANAGEMENT]) is True
        assert user.is_subscription_expired is False

    def test_demo_tier_access_after_expiry(self):
        """Test that Demo Tier blocks access after expiration."""
        expiry = timezone.now() - timedelta(days=1)
        user: Account = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=expiry,
            ),
        )

        # Should NOT have access even to business management
        assert user.has_subscription_tier([Subscription.BUSINESS_MANAGEMENT]) is False
        assert user.is_subscription_expired is True

    def test_demo_time_left_str(self):
        """Test the human-readable time left string."""
        # 2 days left
        expiry = timezone.now() + timedelta(days=2, hours=1)
        user: Account = cast(Account, AccountFactory(subscription_expires_at=expiry))
        assert "2 days remaining" in user.demo_time_left_str

        # 5 hours left
        expiry = timezone.now() + timedelta(hours=5)
        user.subscription_expires_at = expiry
        assert "5 hours remaining" in user.demo_time_left_str

        # Expired
        user.subscription_expires_at = timezone.now() - timedelta(hours=1)
        assert user.demo_time_left_str == "Expired"

    def test_demo_tier_has_project_role(self):
        """Test that active Demo Tier users bypass project role checks."""
        from app.Project.models import Role
        from app.Project.tests.factories import ProjectFactory

        expiry = timezone.now() + timedelta(days=7)
        user: Account = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=expiry,
            ),
        )
        project = ProjectFactory()

        # Should have access to any role (e.g. CONTRACT_VARIATIONS) without explicit assignment
        assert user.has_project_role(project, [Role.CONTRACT_VARIATIONS]) is True

    def test_demo_tier_has_project_role_expired(self):
        """Test that expired Demo Tier users do NOT bypass project role checks."""
        from app.Project.models import Role
        from app.Project.tests.factories import ProjectFactory

        expiry = timezone.now() - timedelta(days=1)
        user: Account = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=expiry,
            ),
        )
        project = ProjectFactory()

        # Should NOT have access since the subscription is expired
        assert user.has_project_role(project, [Role.CONTRACT_VARIATIONS]) is False

    def test_demo_tier_project_roles_filter(self):
        """Test that the projectroles filter bypasses role checks for active Demo Tier."""
        from app.core.templatetags.template_extras import project_roles
        from app.Project.tests.factories import ProjectFactory

        expiry = timezone.now() + timedelta(days=7)
        user: Account = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=expiry,
            ),
        )
        project = ProjectFactory()

        roles = project_roles(user, project)
        # Should return all roles (ProjectRole.objects.all())
        assert roles.exists() is True
