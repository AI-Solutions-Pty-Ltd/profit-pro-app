"""Tests for Demo tier access on consultant views."""

from typing import cast

from django.test import RequestFactory, TestCase

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.Account.tests.factories import AccountFactory
from app.Consultant.views.mixins import ConsultantMixin, PaymentCertMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Company, Project
from app.Project.tests.factories import ClientFactory, ProjectFactory


class TestDemoTierConsultantAccess(TestCase):
    """Test cases for Demo tier access on approvals and consultant pages."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        # User is on DEMO_TIER by default
        self.demo_user: Account = cast(
            Account, AccountFactory(subscription=Subscription.DEMO_TIER)
        )

        # Non-demo user who is NOT a consultant
        self.non_consultant_user: Account = cast(
            Account, AccountFactory(subscription=Subscription.FREE_TIER)
        )

        self.client1 = ClientFactory(name="Client 1", type=Company.Type.CLIENT)
        self.client2 = ClientFactory(name="Client 2", type=Company.Type.CLIENT)

        self.project: Project = cast(
            Project,
            ProjectFactory(
                name="Demo Project", users=[self.demo_user], client=self.client1
            ),
        )

    def test_demo_user_passes_group_permission_mixin(self):
        """Test that active DEMO_TIER users pass group permission checks."""
        mixin = UserHasGroupGenericMixin()
        mixin.permissions = ["consultant"]

        # Request with DEMO_TIER user
        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request

        # Should return True because user is on active DEMO_TIER
        self.assertTrue(mixin.test_func())

    def test_non_demo_user_fails_group_permission_mixin(self):
        """Test that non-consultant, non-demo users fail group permission checks."""
        mixin = UserHasGroupGenericMixin()
        mixin.permissions = ["consultant"]

        # Request with non-consultant, non-demo user
        request = self.factory.get("/")
        request.user = self.non_consultant_user
        mixin.request = request

        # Should return False
        self.assertFalse(mixin.test_func())

    def test_consultant_mixin_returns_all_clients_for_demo_user(self):
        """Test that ConsultantMixin.get_clients returns all clients for DEMO_TIER user."""
        mixin = ConsultantMixin()
        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request

        clients = mixin.get_clients()

        # Should see all CLIENT companies without being a consultant of any
        client_list = list(clients)
        self.assertIn(self.client1, client_list)
        self.assertIn(self.client2, client_list)
        self.assertEqual(len(client_list), 2)

    def test_consultant_mixin_filters_clients_for_non_demo_user(self):
        """Test that ConsultantMixin.get_clients filters clients for non-demo users."""
        mixin = ConsultantMixin()
        request = self.factory.get("/")
        request.user = self.non_consultant_user
        mixin.request = request

        clients = mixin.get_clients()

        # Should see nothing since this user is not a consultant for any company
        self.assertEqual(clients.count(), 0)

    def test_payment_cert_mixin_bypasses_consultant_check_for_demo_user(self):
        """Test that PaymentCertMixin allows DEMO_TIER user to access the project."""
        mixin = PaymentCertMixin()
        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request
        mixin.kwargs = {"project_pk": self.project.pk}

        # Should successfully return project and client
        project = mixin.get_project()
        self.assertEqual(project, self.project)
        self.assertEqual(mixin.get_client(), self.client1)
