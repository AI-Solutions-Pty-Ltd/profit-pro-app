"""Tests for the Demo Tier Expiration Lock-out System (Middleware & View)."""

from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from app.Account.subscription_config import Subscription
from app.Account.tests.factories import AccountFactory, SuperuserFactory


@pytest.mark.django_db
class TestDemoLockout:
    """Test suite verifying the Demo Expiry Lockout system."""

    @pytest.fixture(autouse=True)
    def setup_clients(self):
        """Set up standard pytest clients."""
        self.client = Client()
        self.active_demo_user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=timezone.now() + timedelta(days=5),
        )
        self.expired_demo_user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=timezone.now() - timedelta(days=1),
        )
        self.paid_user = AccountFactory(
            subscription=Subscription.BUSINESS_MANAGEMENT,
        )
        self.superuser = SuperuserFactory()

    def test_active_demo_user_can_access_dashboard(self):
        """Verify that an active demo user can access standard app views."""
        self.client.force_login(self.active_demo_user)
        response = self.client.get(reverse("users:account:user_detail"))
        assert response.status_code == 200

    def test_expired_demo_user_is_locked_out(self):
        """Verify that an expired demo user is redirected to the demo-expired page."""
        self.client.force_login(self.expired_demo_user)
        response = self.client.get(reverse("users:account:user_detail"))

        # Check standard 302 redirect
        assert response.status_code == 302
        assert response.url == reverse("users:account:demo-expired")

    def test_expired_demo_user_can_access_logout_and_demo_expired_views(self):
        """Verify that the middleware permits expired users to access lockout view and logout."""
        self.client.force_login(self.expired_demo_user)

        # Lockout page itself should be accessible
        response_expired = self.client.get(reverse("users:account:demo-expired"))
        assert response_expired.status_code == 200

        # Logout page should not redirect to demo-expired (can be 200 or 302, but not redirecting to lockout)
        response_logout = self.client.get(reverse("users:auth:logout"))
        assert response_logout.status_code != 302 or response_logout.url != reverse(
            "users:account:demo-expired"
        )

    def test_active_user_cannot_access_lockout_view(self):
        """Verify that an active user accessing the demo-expired view is redirected to home."""
        self.client.force_login(self.active_demo_user)
        response = self.client.get(reverse("users:account:demo-expired"))
        assert response.status_code == 302
        assert response.url == reverse("home")

    def test_paid_user_cannot_access_lockout_view(self):
        """Verify that a paid user accessing the demo-expired view is redirected to home."""
        self.client.force_login(self.paid_user)
        response = self.client.get(reverse("users:account:demo-expired"))
        assert response.status_code == 302
        assert response.url == reverse("home")

    def test_superuser_is_not_locked_out(self):
        """Verify that administrators/superusers bypass the demo lockout logic entirely."""
        # Force superuser to have demo tier & expired subscription config
        self.superuser.subscription = Subscription.DEMO_TIER
        self.superuser.subscription_expires_at = timezone.now() - timedelta(days=1)  # ty: ignore[invalid-assignment]
        self.superuser.save()

        self.client.force_login(self.superuser)
        response = self.client.get(reverse("users:account:user_detail"))
        assert response.status_code == 200

    def test_expired_demo_user_ajax_receives_403(self):
        """Verify that AJAX/JSON requests from expired users return 403 instead of 302 HTML redirects."""
        self.client.force_login(self.expired_demo_user)

        # Scenario A: XMLHttpRequest header
        response_ajax = self.client.get(
            reverse("users:account:user_detail"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert response_ajax.status_code == 403
        assert response_ajax.json() == {
            "error": "Demo trial period has expired. Please upgrade your plan."
        }

        # Scenario B: Accept header with application/json
        response_json = self.client.get(
            reverse("users:account:user_detail"), HTTP_ACCEPT="application/json"
        )
        assert response_json.status_code == 403
        assert response_json.json() == {
            "error": "Demo trial period has expired. Please upgrade your plan."
        }

    def test_complimentary_notice_visible_for_paid_user(self):
        """Verify the complimentary notice ribbon is rendered for paid users."""
        self.client.force_login(self.paid_user)
        response = self.client.get(reverse("home"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert (
            "Subscriber Business Management Module with complimentary access" in content
        )
        assert "Complimentary Access Ribbon" in content
        assert 'id="complimentary-access-ribbon"' in content
        assert 'onclick="dismissComplimentaryRibbon()"' in content
        assert "function dismissComplimentaryRibbon" in content
        assert "FOUR_HOURS" in content
        assert "TWO_MINUTES" in content
        assert "complimentary_ribbon_dismissed_at" in content

    def test_complimentary_notice_not_visible_for_demo_user(self):
        """Verify the complimentary notice is not rendered for demo users."""
        self.client.force_login(self.active_demo_user)
        response = self.client.get(reverse("users:account:user_detail"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "with complimentary access" not in content
        assert "Complimentary Access Ribbon" not in content

    def test_complimentary_notice_not_visible_for_anonymous_user(self):
        """Verify the complimentary notice is not rendered for unauthenticated users."""
        response = self.client.get(reverse("home"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "with complimentary access" not in content
        assert "Complimentary Access Ribbon" not in content
