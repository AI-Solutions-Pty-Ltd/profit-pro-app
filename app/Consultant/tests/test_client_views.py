"""Test cases for client list view exclude logic."""

from typing import cast

from django.test import RequestFactory, TestCase

from app.Account.models import Account
from app.Account.tests.factories import AccountFactory
from app.Consultant.views.client_management_views import ClientListView
from app.Project.models import Company, Project
from app.Project.tests.factories import ClientFactory, ProjectFactory


class TestClientListView(TestCase):
    """Test cases for ClientListView."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user: Account = cast(Account, AccountFactory())

        self.client1 = ClientFactory(name="Client 1", type=Company.Type.CLIENT)
        self.client2 = ClientFactory(name="Client 2", type=Company.Type.CLIENT)
        self.client3 = ClientFactory(name="Client 3", type=Company.Type.CLIENT)

        self.project: Project = cast(
            Project, ProjectFactory(name="Project 1", users=[self.user])
        )
        self.project.client = self.client1
        self.project.save()

        self.project2: Project = cast(
            Project, ProjectFactory(name="Project 2", users=[self.user])
        )
        self.project2.client = self.client2
        self.project2.save()

        self.project3: Project = cast(
            Project, ProjectFactory(name="Project 3", users=[self.user])
        )
        self.project3.client = self.client3
        self.project3.save()

    def test_queryset_excludes_assigned_client(self):
        """Test that the queryset excludes the currently assigned client."""
        view = ClientListView()
        request = self.factory.get("/")
        request.user = self.user
        view.request = request
        view.kwargs = {"project_pk": self.project.pk}

        # Initialize the project through the mixin
        view.project = self.project

        queryset = view.get_queryset()

        # Should only return 2 clients (excluding the assigned one)
        self.assertEqual(queryset.count(), 2)

        # Should not contain the assigned client
        client_names = list(queryset.values_list("name", flat=True))
        self.assertNotIn(self.client1.name, client_names)
        self.assertIn(self.client2.name, client_names)
        self.assertIn(self.client3.name, client_names)

    def test_queryset_with_no_assigned_client(self):
        """Test that the queryset returns all clients when none is assigned."""
        # Remove assigned client
        self.project.client = None
        self.project.save()

        view = ClientListView()
        request = self.factory.get("/")
        request.user = self.user
        view.request = request
        view.kwargs = {"project_pk": self.project.pk}

        # Initialize the project through the mixin
        view.project = self.project

        queryset = view.get_queryset()

        # Should return clients assigned on other user projects
        self.assertEqual(queryset.count(), 2)

        # Should contain clients assigned on other projects
        client_names = list(queryset.values_list("name", flat=True))
        self.assertIn(self.client2.name, client_names)
        self.assertIn(self.client3.name, client_names)

    def test_queryset_only_returns_client_type(self):
        """Test that the queryset only returns companies with CLIENT type."""
        contractor = ClientFactory(
            name="Contractor Company", type=Company.Type.CONTRACTOR
        )
        self.project2.contractor = contractor
        self.project2.save()

        view = ClientListView()
        request = self.factory.get("/")
        request.user = self.user
        view.request = request
        view.kwargs = {"project_pk": self.project.pk}

        # Initialize the project through the mixin
        view.project = self.project

        queryset = view.get_queryset()

        # Should only return client companies
        self.assertEqual(queryset.count(), 2)

        # All returned companies should be clients
        for company in queryset:
            self.assertEqual(company.type, Company.Type.CLIENT)


class TestRevealClientFieldView(TestCase):
    """Test cases for RevealClientFieldView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory()
        self.other_user = AccountFactory()

        from app.Project.models import Company, ProjectRole, Role

        self.client_company = ClientFactory(
            name="Test Client Company",
            type=Company.Type.CLIENT,
        )

        self.project = ProjectFactory(
            name="Client Privacy Project",
        )
        self.project.client = self.client_company
        self.project.save()

        # Grant Role.ADMIN to the main test user
        ProjectRole.objects.create(
            project=self.project, user=self.user, role=Role.ADMIN
        )

    def test_reveal_endpoint_success_for_authorized_user(self):
        import json

        from django.urls import reverse

        self.client.force_login(self.user)

        url = reverse(
            "client:client-management:client-reveal-field",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.client_company.pk,
            },
        )

        response = self.client.post(
            url,
            data=json.dumps({"field_name": "registration_number"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    def test_reveal_endpoint_forbidden_for_unauthorized_user(self):
        """Test that an unauthorized user receives 403 Forbidden."""
        import json

        from django.urls import reverse

        self.client.force_login(self.other_user)

        url = reverse(
            "client:client-management:client-reveal-field",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.client_company.pk,
            },
        )

        response = self.client.post(
            url,
            data=json.dumps({"field_name": "registration_number"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_reveal_endpoint_bad_request_for_invalid_field(self):
        """Test that requesting an invalid or non-sensitive field returns 400."""
        import json

        from django.urls import reverse

        self.client.force_login(self.user)

        url = reverse(
            "client:client-management:client-reveal-field",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.client_company.pk,
            },
        )

        response = self.client.post(
            url,
            data=json.dumps({"field_name": "name"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
