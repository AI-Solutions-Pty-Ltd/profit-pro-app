"""Tests for Demo tier access on consultant views."""

from datetime import timedelta
from typing import cast

from django.test import RequestFactory, TestCase
from django.utils import timezone

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

        self.client1 = ClientFactory(name="Client 1", type=Company.Type.CLIENT, created_by=self.demo_user)
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

    def test_consultant_mixin_returns_only_associated_clients_for_demo_user(self):
        """Test that ConsultantMixin.get_clients returns only associated clients for DEMO_TIER user."""
        mixin = ConsultantMixin()
        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request

        clients = mixin.get_clients()

        # Should see associated client (via the project where user is in users)
        # but NOT unrelated self.client2
        client_list = list(clients)
        self.assertIn(self.client1, client_list)
        self.assertNotIn(self.client2, client_list)

    def test_consultant_mixin_does_not_return_global_demo_client_by_default(self):
        """Test that ConsultantMixin.get_clients does not include global Demo Client if not associated."""
        global_demo_client = ClientFactory(name="Demo Client", type=Company.Type.CLIENT)
        mixin = ConsultantMixin()
        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request

        clients = mixin.get_clients()
        self.assertNotIn(global_demo_client, list(clients))

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

    def test_expired_demo_user_fails_group_permission_mixin(self):
        """Test that expired DEMO_TIER users fail group permission checks."""
        mixin = UserHasGroupGenericMixin()
        mixin.permissions = ["consultant"]

        # Set expired trial
        self.demo_user.subscription_expires_at = timezone.now() - timedelta(days=1)
        self.demo_user.save()

        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request

        self.assertFalse(mixin.test_func())

    def test_consultant_mixin_filters_clients_for_expired_demo_user(self):
        """Test that ConsultantMixin.get_clients filters clients for expired DEMO_TIER users."""
        mixin = ConsultantMixin()
        self.demo_user.subscription_expires_at = timezone.now() - timedelta(days=1)
        self.demo_user.save()

        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request

        clients = mixin.get_clients()
        self.assertEqual(clients.count(), 0)

    def test_payment_cert_mixin_raises_404_for_expired_demo_user(self):
        """Test that PaymentCertMixin blocks expired DEMO_TIER users."""
        from django.http import Http404

        mixin = PaymentCertMixin()
        self.demo_user.subscription_expires_at = timezone.now() - timedelta(days=1)
        self.demo_user.save()

        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request
        mixin.kwargs = {"project_pk": self.project.pk}

        with self.assertRaises(Http404):
            mixin.get_project()

    def test_payment_cert_mixin_blocks_unassociated_private_project_for_demo_user(self):
        """Test that PaymentCertMixin blocks DEMO_TIER user from accessing unrelated private projects."""
        from django.http import Http404

        unrelated_project = ProjectFactory(
            name="Private Project", client=self.client2
        )  # No users/roles associated with demo user

        mixin = PaymentCertMixin()
        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request
        mixin.kwargs = {"project_pk": unrelated_project.pk}

        with self.assertRaises(Http404):
            mixin.get_project()


class TestCreatorOwnershipRestrictions(TestCase):
    """Test creator ownership restrictions for clients and users."""

    def setUp(self):
        self.factory = RequestFactory()
        self.creator: Account = cast(Account, AccountFactory(email="creator@test.com"))
        self.other_user: Account = cast(Account, AccountFactory(email="other@test.com"))
        self.superuser: Account = cast(Account, AccountFactory(email="admin@test.com", is_superuser=True, is_staff=True))

        self.client_created_by_creator = ClientFactory(
            name="Creator's Client", type=Company.Type.CLIENT, created_by=self.creator
        )
        self.client_created_by_other = ClientFactory(
            name="Other's Client", type=Company.Type.CLIENT, created_by=self.other_user
        )

    def test_client_list_filters_by_creator(self):
        """Test that non-superuser only sees clients they created."""
        from app.Consultant.views.mixins import ClientMixin
        mixin = ClientMixin()
        
        # Creator sees only their client
        request = self.factory.get("/")
        request.user = self.creator
        mixin.request = request
        qs = mixin.get_queryset()
        self.assertIn(self.client_created_by_creator, qs)
        self.assertNotIn(self.client_created_by_other, qs)

        # Other user sees only their client
        request = self.factory.get("/")
        request.user = self.other_user
        mixin.request = request
        qs = mixin.get_queryset()
        self.assertNotIn(self.client_created_by_creator, qs)
        self.assertIn(self.client_created_by_other, qs)

        # Superuser sees all clients
        request = self.factory.get("/")
        request.user = self.superuser
        mixin.request = request
        qs = mixin.get_queryset()
        self.assertIn(self.client_created_by_creator, qs)
        self.assertIn(self.client_created_by_other, qs)

    def test_client_detail_raises_404_for_non_creator(self):
        """Test that ClientMixin.get_object raises 404 for clients not created by user."""
        from django.http import Http404
        from app.Consultant.views.mixins import ClientMixin
        
        mixin = ClientMixin()
        request = self.factory.get("/")
        request.user = self.creator
        mixin.request = request
        
        # Creator can access their client
        mixin.kwargs = {"pk": self.client_created_by_creator.pk}
        obj = mixin.get_object()
        self.assertEqual(obj, self.client_created_by_creator)

        # Creator cannot access other's client
        mixin.kwargs = {"pk": self.client_created_by_other.pk}
        with self.assertRaises(Http404):
            mixin.get_object()

        # Superuser can access any client
        mixin.request.user = self.superuser
        obj = mixin.get_object()
        self.assertEqual(obj, self.client_created_by_other)

