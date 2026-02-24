"""Test cases for contractor list view exclude logic."""

from typing import cast

from django.test import RequestFactory, TestCase

from app.Account.models import Account
from app.Account.tests.factories import AccountFactory
from app.Project.models import Company, Project
from app.Project.tests.factories import ClientFactory, ProjectFactory
from app.Consultant.views.contractor_management_views import ContractorListView


class TestContractorListView(TestCase):
    """Test cases for ContractorListView."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user: Account = cast(Account, AccountFactory())

        self.contractor1 = ClientFactory(
            name="Contractor 1",
            type=Company.Type.CONTRACTOR,
        )
        self.contractor2 = ClientFactory(
            name="Contractor 2",
            type=Company.Type.CONTRACTOR,
        )
        self.contractor3 = ClientFactory(
            name="Contractor 3",
            type=Company.Type.CONTRACTOR,
        )

        self.project: Project = cast(
            Project, ProjectFactory(name="Project 1", users=[self.user])
        )
        self.project.contractor = self.contractor1
        self.project.save()

        self.project2: Project = cast(
            Project, ProjectFactory(name="Project 2", users=[self.user])
        )
        self.project2.contractor = self.contractor2
        self.project2.save()

        self.project3: Project = cast(
            Project, ProjectFactory(name="Project 3", users=[self.user])
        )
        self.project3.contractor = self.contractor3
        self.project3.save()

    def test_queryset_excludes_assigned_contractor(self):
        """Test that the queryset excludes the currently assigned contractor."""
        view = ContractorListView()
        request = self.factory.get("/")
        request.user = self.user
        view.request = request
        view.kwargs = {"project_pk": self.project.pk}

        # Initialize the project through the mixin
        view.project = self.project

        queryset = view.get_queryset()

        # Should only return 2 contractors (excluding the assigned one)
        self.assertEqual(queryset.count(), 2)

        # Should not contain the assigned contractor
        contractor_names = list(queryset.values_list("name", flat=True))
        self.assertNotIn(self.contractor1.name, contractor_names)
        self.assertIn(self.contractor2.name, contractor_names)
        self.assertIn(self.contractor3.name, contractor_names)

    def test_queryset_with_no_assigned_contractor(self):
        """Test that the queryset returns all contractors when none is assigned."""
        # Remove assigned contractor
        self.project.contractor = None
        self.project.save()

        view = ContractorListView()
        request = self.factory.get("/")
        request.user = self.user
        view.request = request
        view.kwargs = {"project_pk": self.project.pk}

        # Initialize the project through the mixin
        view.project = self.project

        queryset = view.get_queryset()

        # Should return contractors from other user projects
        self.assertEqual(queryset.count(), 2)

        # Should contain contractors assigned on other projects
        contractor_names = list(queryset.values_list("name", flat=True))
        self.assertIn(self.contractor2.name, contractor_names)
        self.assertIn(self.contractor3.name, contractor_names)

    def test_queryset_only_returns_contractor_type(self):
        """Test that the queryset only returns companies with CONTRACTOR type."""
        client = ClientFactory(name="Client Company", type=Company.Type.CLIENT)
        self.project2.client = client
        self.project2.save()

        view = ContractorListView()
        request = self.factory.get("/")
        request.user = self.user
        view.request = request
        view.kwargs = {"project_pk": self.project.pk}

        # Initialize the project through the mixin
        view.project = self.project

        queryset = view.get_queryset()

        # Should only return contractor companies
        self.assertEqual(queryset.count(), 2)

        # All returned companies should be contractors
        for company in queryset:
            self.assertEqual(company.type, Company.Type.CONTRACTOR)
