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
        expiry = timezone.now() + timedelta(hours=5, seconds=10)
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
        project = ProjectFactory(is_demo=True)

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
        project = ProjectFactory(is_demo=True)

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

    def test_has_demo_permission_active(self):
        """Test that has_demo_permission is True for active trials."""
        expiry = timezone.now() + timedelta(days=5)
        user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=expiry,
        )
        assert user.has_demo_permission is True

    def test_has_demo_permission_expired(self):
        """Test that has_demo_permission is False for expired trials."""
        expiry = timezone.now() - timedelta(days=1)
        user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=expiry,
        )
        assert user.has_demo_permission is False

    def test_has_demo_permission_other_tier(self):
        """Test that has_demo_permission is False for other active tiers."""
        user = AccountFactory(subscription=Subscription.BUSINESS_MANAGEMENT)
        assert user.has_demo_permission is False

    def test_has_demo_permission_no_expiry(self):
        """Test that has_demo_permission handles None expiry dates gracefully."""
        user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=None,
        )
        assert user.has_demo_permission is True

    def test_demo_tier_project_roles_filter_expired(self):
        """Test that the projectroles filter does NOT bypass role checks for expired trials."""
        from app.core.templatetags.template_extras import project_roles
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

        roles = project_roles(user, project)
        # Should not return all roles; since user is not assigned to the project, should be empty/filtered
        assert roles.exists() is False


@pytest.mark.django_db
class TestFullAccessTier:
    """Test cases for the new non-expiring Full Access Tier behavior."""

    def test_full_access_tier_has_subscription_tier(self):
        """Test that Full Access Tier satisfies any required subscription checks."""
        user: Account = cast(
            Account,
            AccountFactory(subscription=Subscription.FULL_ACCESS),
        )
        assert user.has_subscription_tier([Subscription.BUSINESS_MANAGEMENT]) is True

    def test_full_access_tier_has_demo_permission(self):
        """Test that Full Access Tier has full access / demo bypass permission."""
        user: Account = cast(
            Account,
            AccountFactory(subscription=Subscription.FULL_ACCESS),
        )
        assert user.has_demo_permission is True

    def test_full_access_tier_is_not_expired(self):
        """Test that Full Access Tier never expires, even with old or None expiry dates."""
        past_expiry = timezone.now() - timedelta(days=10)
        user: Account = cast(
            Account,
            AccountFactory(
                subscription=Subscription.FULL_ACCESS,
                subscription_expires_at=past_expiry,
            ),
        )
        assert user.is_subscription_expired is False
        assert user.has_demo_permission is True

    def test_full_access_tier_bypasses_project_role_checks(self):
        """Test that Full Access Tier users bypass role checks in their assigned demo projects."""
        from app.Project.models import Role
        from app.Project.tests.factories import ProjectFactory

        user: Account = cast(
            Account,
            AccountFactory(subscription=Subscription.FULL_ACCESS),
        )
        project = ProjectFactory(is_demo=True)
        assert user.has_project_role(project, [Role.CONTRACT_VARIATIONS]) is True

    def test_full_access_tier_data_isolation(self):
        """Test that Full Access Tier preserves multi-tenant data isolation."""
        from app.Project.tests.factories import ProjectFactory

        user: Account = cast(
            Account,
            AccountFactory(subscription=Subscription.FULL_ACCESS),
        )
        # Unrelated project
        unrelated_project = ProjectFactory()

        # The user is not in the project users or project roles, so they should not get it in their list
        assert unrelated_project not in user.get_projects


@pytest.mark.django_db
class TestDemo123Project:
    """Test cases for the special 'demo 123' project scoping and read-only behavior."""

    def test_demo_123_visible_to_demo_tier_user(self):
        """Test that active and expired Demo Tier users see the 'demo 123' project."""
        from app.Project.tests.factories import ProjectFactory

        demo_user = AccountFactory(subscription=Subscription.DEMO_TIER)
        demo_123 = ProjectFactory(name="demo 123", is_demo=False)

        assert demo_123 in demo_user.get_projects

    def test_demo_123_not_visible_to_other_users(self):
        """Test that non-demo tier, non-staff users do NOT see 'demo 123'."""
        from app.Project.tests.factories import ProjectFactory

        free_user = AccountFactory(subscription=Subscription.FREE_TIER)
        demo_123 = ProjectFactory(name="demo 123", is_demo=False)

        assert demo_123 not in free_user.get_projects

    def test_demo_123_read_only_for_demo_tier_user(self):
        """Test that demo tier users have read-only access (GET permitted, POST/mutation blocked)."""
        from django.test import RequestFactory

        from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
        from app.Project.models import Role
        from app.Project.tests.factories import ProjectFactory

        # Create an active demo user
        demo_user: Account = cast(
            Account,
            AccountFactory(
                subscription=Subscription.DEMO_TIER,
                subscription_expires_at=timezone.now() + timedelta(days=7),
            ),
        )
        demo_123 = ProjectFactory(name="demo 123", is_demo=False)

        # 1. Check role bypass
        assert demo_user.has_project_role(demo_123, [Role.CONTRACT_VARIATIONS]) is True

        # 2. Check read-only blocks in mixin
        class DummyView(UserHasProjectRoleGenericMixin):
            roles = [Role.CONTRACT_VARIATIONS]
            project_slug = "project_pk"

        view = DummyView()
        view.kwargs = {"project_pk": demo_123.pk}

        factory = RequestFactory()

        # GET request should pass test_func
        request_get = factory.get(f"/projects/{demo_123.pk}/")
        request_get.user = demo_user
        view.request = request_get
        assert view.test_func() is True

        # POST request should NOT pass (it is blocked / read-only)
        request_post = factory.post(f"/projects/{demo_123.pk}/")
        request_post.user = demo_user
        view.request = request_post
        assert view.test_func() is False
