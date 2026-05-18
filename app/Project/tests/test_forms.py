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

    def test_form_includes_newly_created_contractor_associated_with_user(self):
        """Test that a newly created contractor (not assigned to any projects yet but linked to user) is included."""
        new_contractor = ClientFactory(
            name="New Contractor XYZ",
            type=Company.Type.CONTRACTOR,
        )
        new_contractor.users.add(self.user)

        form = ProjectContractorForm(user=self.user, project=self.project)
        queryset = form.fields["contractor"].queryset  # type: ignore

        # Should show contractor2 (active on project2) AND new_contractor (linked to user)
        self.assertEqual(queryset.count(), 2)

        contractor_names = list(queryset.values_list("name", flat=True))
        self.assertIn("New Contractor XYZ", contractor_names)
        self.assertIn(self.contractor2.name, contractor_names)
        self.assertNotIn(self.contractor1.name, contractor_names)


class TestContractorQuickCreateForm(TestCase):
    """Test cases for ContractorQuickCreateForm."""

    def test_quick_create_form_fields(self):
        """Test that the quick create form matches CompanyForm and has correct fields."""
        from app.Project.company.company_forms import CompanyForm
        from app.Project.forms.forms import ContractorQuickCreateForm

        form = ContractorQuickCreateForm()
        # Verify it inherits from CompanyForm
        self.assertTrue(isinstance(form, CompanyForm))

        # Should have name, logo, and users but NOT consultants
        self.assertIn("name", form.fields)
        self.assertIn("logo", form.fields)
        self.assertIn("users", form.fields)
        self.assertNotIn("consultants", form.fields)

    def test_quick_create_form_save(self):
        """Test that saving the form sets the company type to CONTRACTOR."""
        from app.Project.forms.forms import ContractorQuickCreateForm

        data = {
            "name": "Quick Contractor Ltd",
            "registration_number": "123456",
        }
        form = ContractorQuickCreateForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        company = form.save()
        self.assertEqual(company.name, "Quick Contractor Ltd")
        self.assertEqual(company.type, Company.Type.CONTRACTOR)


class TestCompanyFormPrivacy(TestCase):
    """Test cases for CompanyForm privacy features."""

    def setUp(self):
        """Set up test data."""
        self.user: Account = cast(
            Account,
            AccountFactory(
                first_name="John", last_name="Doe", email="john@example.com"
            ),
        )

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
            bank_swift_code="ABSAZAJJ123",
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

    def test_company_form_excludes_nameless_users(self):
        """Test that users without a first name and last name are excluded from querysets."""
        from app.Project.company.company_forms import CompanyForm

        user_with_name = AccountFactory(first_name="Alice", last_name="Smith")
        user_without_name = AccountFactory(first_name="", last_name="")

        form = CompanyForm(contractor=False)
        users_queryset = form.fields["users"].queryset
        consultants_queryset = form.fields["consultants"].queryset

        self.assertIn(user_with_name, users_queryset)
        self.assertNotIn(user_without_name, users_queryset)
        self.assertIn(user_with_name, consultants_queryset)
        self.assertNotIn(user_without_name, consultants_queryset)
