"""Tests for the Demo Tier and subscription expiration logic."""

import pytest
from django.utils import timezone
from datetime import timedelta

from app.Account.tests.factories import AccountFactory
from app.Account.subscription_config import Subscription

@pytest.mark.django_db
class TestDemoTier:
    """Test cases for Demo Tier behavior."""

    def test_demo_tier_access_before_expiry(self):
        """Test that Demo Tier grants access before expiration."""
        expiry = timezone.now() + timedelta(days=7)
        user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=expiry
        )
        
        # Should have access to business management (parent of demo)
        assert user.has_subscription_tier([Subscription.BUSINESS_MANAGEMENT]) is True
        assert user.is_subscription_expired is False

    def test_demo_tier_access_after_expiry(self):
        """Test that Demo Tier blocks access after expiration."""
        expiry = timezone.now() - timedelta(days=1)
        user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=expiry
        )
        
        # Should NOT have access even to business management
        assert user.has_subscription_tier([Subscription.BUSINESS_MANAGEMENT]) is False
        assert user.is_subscription_expired is True

    def test_demo_time_left_str(self):
        """Test the human-readable time left string."""
        # 2 days left
        expiry = timezone.now() + timedelta(days=2, hours=1)
        user = AccountFactory(subscription_expires_at=expiry)
        assert "2 days remaining" in user.demo_time_left_str

        # 5 hours left
        expiry = timezone.now() + timedelta(hours=5)
        user.subscription_expires_at = expiry
        assert "5 hours remaining" in user.demo_time_left_str

        # Expired
        user.subscription_expires_at = timezone.now() - timedelta(hours=1)
        assert user.demo_time_left_str == "Expired"
