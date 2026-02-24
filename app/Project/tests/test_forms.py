"""Test cases for ProjectContractorForm parameter handling."""

from typing import cast

from django.test import TestCase

from app.Account.models import Account
from app.Account.tests.factories import AccountFactory
from app.Project.forms import ProjectContractorForm
from app.Project.models import Company, Project
from app.Project.tests.factories import ClientFactory, ProjectFactory


class TestProjectContractorForm(TestCase):
    """Test cases for ProjectContractorForm."""

    def setUp(self):
        """Set up test data."""
        self.user: Account = cast(Account, AccountFactory())

        self.contractor1 = ClientFactory(
            name="Contractor 1",
            type=Company.Type.CONTRACTOR,
        )
        self.contractor2 = ClientFactory(
            name="Contractor 2",
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

    def test_form_requires_user_parameter(self):
        """Test that the form requires a user parameter."""
        with self.assertRaises(AttributeError):
            # This should fail because user is None
            ProjectContractorForm(user=None)

    def test_form_filters_by_user_projects(self):
        """Test that the form filters contractors by user's projects."""
        form = ProjectContractorForm(user=self.user, project=self.project)
        queryset = form.fields["contractor"].queryset  # type: ignore

        # Should only return contractors associated with user's projects
        self.assertEqual(queryset.count(), 1)

        # Should exclude the assigned contractor
        contractor_names = list(queryset.values_list("name", flat=True))
        self.assertNotIn(self.contractor1.name, contractor_names)
        self.assertIn(self.contractor2.name, contractor_names)

    def test_form_without_project_shows_all_contractors(self):
        """Test that the form shows all contractors when no project is provided."""
        form = ProjectContractorForm(user=self.user)
        queryset = form.fields["contractor"].queryset  # type: ignore

        # Should return all contractors associated with user's projects
        self.assertEqual(queryset.count(), 2)

        contractor_names = list(queryset.values_list("name", flat=True))
        self.assertIn(self.contractor1.name, contractor_names)
        self.assertIn(self.contractor2.name, contractor_names)
