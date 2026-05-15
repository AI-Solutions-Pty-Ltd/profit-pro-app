"""Tests for Estimator views."""

import pytest
from django.urls import reverse

from app.Account.subscription_config import Subscription
from app.Account.tests.factories import AccountFactory


@pytest.mark.django_db
class TestContractorLibraryAccess:
    """Test cases for Contractor Library access control."""

    def test_free_tier_access_without_company(self, client):
        """Test that a Free tier user can access the library even without a company."""
        user = AccountFactory(subscription=Subscription.FREE_TIER)
        client.force_login(user)

        # Access the Contractor Library (Trade Codes view)
        url = reverse("estimator:ctr_trade_codes")
        response = client.get(url)

        # Should be 200 OK (accessible but empty) instead of 403 Forbidden
        assert response.status_code == 200

    def test_demo_tier_access_without_company(self, client):
        """Test that a Demo tier user can access the library even without a company."""
        user = AccountFactory(subscription=Subscription.DEMO_TIER)
        client.force_login(user)

        url = reverse("estimator:ctr_trade_codes")
        response = client.get(url)

        assert response.status_code == 200

    def test_other_tier_access_without_company(self, client):
        """Test that other tiers still require a company (or staff status)."""
        # Site Management tier doesn't automatically grant library access without a company
        user = AccountFactory(subscription=Subscription.SITE_MANAGEMENT)
        client.force_login(user)

        url = reverse("estimator:ctr_trade_codes")
        response = client.get(url)

        # Should be 403 Forbidden because they aren't in Free/Demo and have no company
        assert response.status_code == 403
