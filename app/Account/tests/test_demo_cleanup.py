"""Tests for the Demo Tier Expiration Cleanup System."""

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from app.Account.subscription_config import Subscription
from app.Account.tests.factories import AccountFactory
from app.Project.models import Company, Project
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestDemoCleanup:
    """Test suite verifying the cleanup of demo companies on trial expiration."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Set up standard pytest clients and test accounts."""
        self.client = Client()

        # 1. Create an expired demo user
        self.expired_user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=timezone.now() - timedelta(days=1),
        )
        # Populate their demo companies
        self.expired_user_companies = Company.ensure_demo_companies(self.expired_user)
        # Create a project associated with these demo companies
        self.expired_project = ProjectFactory(
            client=self.expired_user_companies[0],
            contractor=self.expired_user_companies[1],
            lead_consultant=self.expired_user_companies[2],
        )

        # 2. Create an active (non-expired) demo user
        self.active_user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=timezone.now() + timedelta(days=5),
        )
        self.active_user_companies = Company.ensure_demo_companies(self.active_user)
        self.active_project = ProjectFactory(
            client=self.active_user_companies[0],
            contractor=self.active_user_companies[1],
            lead_consultant=self.active_user_companies[2],
        )

    def test_clean_demo_companies_direct_deletion(self):
        """Verify that clean_demo_companies classmethod hard-deletes scoped companies."""
        # Before clean: verify companies exist in DB
        user_pks = [c.pk for c in self.expired_user_companies]
        assert Company.all_objects.filter(pk__in=user_pks).count() == 3

        # Clean companies
        deleted_count = Company.clean_demo_companies(self.expired_user)
        assert deleted_count == 3

        # After clean: verify companies are hard-deleted
        assert Company.all_objects.filter(pk__in=user_pks).count() == 0

    def test_project_cascade_safety_set_null(self):
        """Verify that deleting demo companies sets ForeignKey fields to None on Projects without deleting the Projects."""
        # Verify initial foreign keys are set
        self.expired_project.refresh_from_db()
        assert self.expired_project.client is not None
        assert self.expired_project.contractor is not None
        assert self.expired_project.lead_consultant is not None

        # Clean demo companies
        Company.clean_demo_companies(self.expired_user)

        # Verify project is NOT deleted and fields are set to None
        self.expired_project.refresh_from_db()
        assert Project.objects.filter(pk=self.expired_project.pk).exists() is True
        assert self.expired_project.client is None
        assert self.expired_project.contractor is None
        assert self.expired_project.lead_consultant is None

    def test_active_demo_users_are_not_affected(self):
        """Verify that clean_demo_companies does not touch active demo users' companies or projects."""
        # Run clean on expired user
        Company.clean_demo_companies(self.expired_user)

        # Verify active user's companies still exist
        active_pks = [c.pk for c in self.active_user_companies]
        assert Company.objects.filter(pk__in=active_pks).count() == 3

        # Verify active user's project remains untouched
        self.active_project.refresh_from_db()
        assert self.active_project.client is not None
        assert self.active_project.contractor is not None
        assert self.active_project.lead_consultant is not None

    def test_lockout_view_triggers_realtime_cleanup(self):
        """Verify that landing on the demo-expired page triggers clean_demo_companies for the expired user."""
        self.client.force_login(self.expired_user)

        # Landing on the page
        response = self.client.get(reverse("users:account:demo-expired"))
        assert response.status_code == 200

        # Verify companies are cleaned in real-time
        expired_pks = [c.pk for c in self.expired_user_companies]
        assert Company.all_objects.filter(pk__in=expired_pks).count() == 0

        # Verify active demo user's companies remain intact
        active_pks = [c.pk for c in self.active_user_companies]
        assert Company.objects.filter(pk__in=active_pks).count() == 3

    def test_cleanup_command_bulk_purges_expired_data(self):
        """Verify that clean_expired_demo_companies command cleans demo companies for all expired users in bulk."""
        # Create another expired user with demo companies
        another_expired = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=timezone.now() - timedelta(days=2),
        )
        another_companies = Company.ensure_demo_companies(another_expired)

        # Verify their companies exist
        expired_pks = [c.pk for c in self.expired_user_companies] + [
            c.pk for c in another_companies
        ]
        assert Company.all_objects.filter(pk__in=expired_pks).count() == 6

        # Call bulk cleanup command
        call_command("clean_expired_demo_companies")

        # Verify all expired companies are purged
        assert Company.all_objects.filter(pk__in=expired_pks).count() == 0

        # Verify active user's companies remain unaffected
        active_pks = [c.pk for c in self.active_user_companies]
        assert Company.objects.filter(pk__in=active_pks).count() == 3

    def test_cleanup_is_idempotent_and_safe(self):
        """Verify that running cleanup multiple times is safe and doesn't throw errors."""
        # Run cleanup first time
        deleted_1 = Company.clean_demo_companies(self.expired_user)
        assert deleted_1 == 3

        # Run cleanup second time (should be idempotent)
        deleted_2 = Company.clean_demo_companies(self.expired_user)
        assert (
            deleted_2 == 0
        )  # No companies left to delete, but runs safely with 0 errors
