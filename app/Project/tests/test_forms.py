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

    def test_form_works_with_none_user(self):
        """Test that the form works even if user is None (uses fallback)."""
        form = ProjectContractorForm(user=None)
        queryset = form.fields["contractor"].queryset  # type: ignore
        # Fallback should show all contractors
        self.assertEqual(queryset.count(), 2)

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


class TestCompanyFormPrivacy(TestCase):
    """Test cases for CompanyForm privacy features."""

    def setUp(self):
        """Set up test data."""
        self.user: Account = cast(Account, AccountFactory(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        ))

    def test_company_form_uses_privacy_user_field(self):
        """Test that the users field represents names instead of emails."""
        from app.Project.company.company_forms import CompanyForm
        form = CompanyForm(contractor=True)
        # Check label is displayed as name instead of email
        label = form.fields["users"].label_from_instance(self.user)
        self.assertEqual(label, "John Doe")

    def test_company_form_masks_initial_sensitive_data(self):
        """Test that initial sensitive fields are masked to show last 4 chars."""
        from app.Project.company.company_forms import CompanyForm
        company = ClientFactory(
            name="Contractor XYZ",
            type=Company.Type.CONTRACTOR,
            registration_number="1234567890",
            tax_number="TAX-998877",
            vat_number="VAT-776655",
            bank_account_number="9876543210",
            bank_branch_code="198765",
            bank_swift_code="ABSAZAJJ123"
        )
        form = CompanyForm(instance=company, contractor=True)
        self.assertEqual(form.initial["registration_number"], "••••••7890")
        self.assertEqual(form.initial["tax_number"], "••••••8877")
        self.assertEqual(form.initial["bank_swift_code"], "•••••••J123")


    def test_company_form_clean_preserves_masked_values(self):
        """Test that submitting a masked value does not overwrite database value."""
        from app.Project.company.company_forms import CompanyForm
        company = ClientFactory(
            name="Contractor XYZ",
            type=Company.Type.CONTRACTOR,
            registration_number="1234567890",
        )
        # Post the masked registration number along with other required fields
        data = {
            "name": "Contractor XYZ",
            "registration_number": "••••••7890",
        }
        form = CompanyForm(data=data, instance=company, contractor=True)
        self.assertTrue(form.is_valid(), form.errors)
        saved_instance = form.save()
        self.assertEqual(saved_instance.registration_number, "1234567890")

