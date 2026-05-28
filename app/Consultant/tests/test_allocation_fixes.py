"""Test cases for Lead Consultant and Client allocation, quick-create, and filtering fixes."""

from django.test import RequestFactory, TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Consultant.forms import ProjectClientForm
from app.Project.forms.forms import (
    ClientQuickCreateForm,
    LeadConsultantQuickCreateForm,
    ProjectLeadConsultantForm,
)
from app.Project.models import Company, Project, ProjectRole, Role
from app.Project.tests.factories import ClientFactory, ProjectFactory


class TestAllocationFixes(TestCase):
    """Test suite verifying Lead Consultant and Client allocation and quick-create fixes."""

    def setUp(self):
        """Set up test environment and database records."""
        self.factory = RequestFactory()
        self.user = AccountFactory()

        # Create client and lead consultant companies
        self.client_company: Company = ClientFactory(  # type: ignore
            name="Test Client Company",
            type=Company.Type.CLIENT,
        )
        self.lead_consultant_company: Company = ClientFactory(  # type: ignore
            name="Test Lead Consultant Company",
            type=Company.Type.LEAD_CONSULTANT,
        )

        self.project: Project = ProjectFactory(  # type: ignore
            name="Allocation Test Project",
            client=None,
        )
        # Link project and user
        self.project.users.add(self.user)
        ProjectRole.objects.create(
            project=self.project,
            user=self.user,
            role=Role.ADMIN,
        )

    def test_client_quick_create_form_fields(self):
        """Verify that ClientQuickCreateForm subclasses CompanyForm and includes all detailed fields."""
        form = ClientQuickCreateForm()
        # Verify it has banking, registration, tax, vat, etc.
        self.assertIn("bank_account_number", form.fields)
        self.assertIn("bank_branch_code", form.fields)
        self.assertIn("tax_number", form.fields)
        self.assertIn("vat_number", form.fields)

    def test_lead_consultant_quick_create_form_fields(self):
        """Verify that LeadConsultantQuickCreateForm subclasses CompanyForm and includes all detailed fields."""
        form = LeadConsultantQuickCreateForm()
        # Verify it has banking, registration, tax, vat, etc.
        self.assertIn("bank_account_number", form.fields)
        self.assertIn("bank_branch_code", form.fields)
        self.assertIn("tax_number", form.fields)
        self.assertIn("vat_number", form.fields)

    def test_project_client_form_queryset_filtering(self):
        """Verify that ProjectClientForm filters queryset using the user's projects and account."""
        # When user is not provided
        form_no_user = ProjectClientForm(project=self.project)
        # Fallback query gets all client companies
        self.assertIn(self.client_company, form_no_user.fields["client"].queryset)

        # When user is provided and client is linked to user
        self.client_company.users.add(self.user)
        form_with_user = ProjectClientForm(project=self.project, user=self.user)
        self.assertIn(self.client_company, form_with_user.fields["client"].queryset)

    def test_project_lead_consultant_form_queryset_filtering(self):
        """Verify that ProjectLeadConsultantForm filters queryset using the user's projects and account."""
        # When user is not provided
        form_no_user = ProjectLeadConsultantForm(project=self.project)
        # Fallback query gets all lead consultant companies
        self.assertIn(
            self.lead_consultant_company,
            form_no_user.fields["lead_consultant"].queryset,
        )

        # When user is provided and lead consultant is linked to user
        self.lead_consultant_company.users.add(self.user)
        form_with_user = ProjectLeadConsultantForm(project=self.project, user=self.user)
        self.assertIn(
            self.lead_consultant_company,
            form_with_user.fields["lead_consultant"].queryset,
        )

    def test_project_client_form_includes_currently_assigned_client(self):
        """Verify that ProjectClientForm includes the currently assigned client in its queryset."""
        self.project.client = self.client_company
        self.project.save()

        # Check with user
        self.client_company.users.add(self.user)
        form = ProjectClientForm(project=self.project, user=self.user)
        self.assertIn(self.client_company, form.fields["client"].queryset)

        # Check without user
        form_no_user = ProjectClientForm(project=self.project)
        self.assertIn(self.client_company, form_no_user.fields["client"].queryset)

    def test_project_lead_consultant_form_includes_currently_assigned_lead_consultant(
        self,
    ):
        """Verify that ProjectLeadConsultantForm includes the currently assigned lead consultant."""
        self.project.lead_consultant = self.lead_consultant_company
        self.project.save()

        # Check with user
        self.lead_consultant_company.users.add(self.user)
        form = ProjectLeadConsultantForm(project=self.project, user=self.user)
        self.assertIn(
            self.lead_consultant_company, form.fields["lead_consultant"].queryset
        )

        # Check without user
        form_no_user = ProjectLeadConsultantForm(project=self.project)
        self.assertIn(
            self.lead_consultant_company,
            form_no_user.fields["lead_consultant"].queryset,
        )

    def test_client_quick_create_save_with_m2m(self):
        """Verify saving ClientQuickCreateForm saves type and many-to-many associations correctly."""
        form = ClientQuickCreateForm(
            data={
                "name": "New Quick Client",
                "registration_number": "123456789",
                "bank_account_number": "987654321",
                "bank_branch_code": "250655",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        client = form.save()
        self.assertEqual(client.type, Company.Type.CLIENT)
        self.assertEqual(client.registration_number, "123456789")
        self.assertEqual(client.bank_account_number, "987654321")

    def test_lead_consultant_quick_create_save_with_m2m(self):
        """Verify saving LeadConsultantQuickCreateForm saves type and many-to-many associations correctly."""
        form = LeadConsultantQuickCreateForm(
            data={
                "name": "New Quick Lead Consultant",
                "registration_number": "987654",
                "bank_account_number": "11223344",
                "bank_branch_code": "123456",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        lead_consultant = form.save()
        self.assertEqual(lead_consultant.type, Company.Type.LEAD_CONSULTANT)
        self.assertEqual(lead_consultant.registration_number, "987654")
        self.assertEqual(lead_consultant.bank_account_number, "11223344")

    def test_lead_consultant_delete_view_nonexistent_returns_404(self):
        """Verify that requesting a nonexistent lead consultant ID returns 404 instead of throwing DoesNotExist."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "client:lead-consultant-management:lead-consultant-delete",
                kwargs={"project_pk": self.project.pk, "pk": 99999},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_client_update_view_nonexistent_returns_404(self):
        """Verify that requesting a nonexistent client ID returns 404 instead of throwing DoesNotExist."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "client:client-management:client-update",
                kwargs={"project_pk": self.project.pk, "pk": 99999},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_contractor_update_view_nonexistent_returns_404(self):
        """Verify that requesting a nonexistent contractor ID returns 404 instead of throwing DoesNotExist."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "client:contractor-management:contractor-update",
                kwargs={"project_pk": self.project.pk, "pk": 99999},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_quick_create_company_associates_both_users_and_consultants(self):
        """Verify that dynamic quick-create associates the current user to both users and consultants relations."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("dynamic-quick-create-submit"),
            data={
                "resource_type": "client",
                "name": "Quick Created Client XYZ",
                "registration_number": "REG-XYZ",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"), data)
        company_id = data.get("id")
        company = Company.objects.get(pk=company_id)

        # Verify the user is in both users and consultants
        self.assertIn(self.user, company.users.all())
        self.assertIn(self.user, company.consultants.all())
