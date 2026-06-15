"""Test cases for Lead Consultant and Client allocation, quick-create, and filtering fixes."""

from django.test import RequestFactory, TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Consultant.forms import ProjectClientForm
from app.Project.forms.forms import (
    ClientQuickCreateForm,
    LeadConsultantQuickCreateForm,
    ProjectConsultantForm,
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

    def test_project_consultant_form_queryset_filtering(self):
        """Verify that ProjectConsultantForm filters queryset to include both LEAD_CONSULTANT and CONSULTANT."""
        consultant_company = ClientFactory(
            name="Test Consultant Company",
            type=Company.Type.CONSULTANT,
        )
        # Check without user
        form = ProjectConsultantForm(project=self.project)
        self.assertIn(consultant_company, form.fields["consultant"].queryset)
        self.assertIn(self.lead_consultant_company, form.fields["consultant"].queryset)

    def test_project_consultant_properties(self):
        """Verify the new lead_consultant_companies and regular_consultant_companies properties on Project."""
        consultant_company = ClientFactory(
            name="Test Consultant Company",
            type=Company.Type.CONSULTANT,
        )
        self.project.consultants.add(self.lead_consultant_company)
        self.project.consultants.add(consultant_company)

        self.assertIn(self.lead_consultant_company, self.project.lead_consultant_companies)
        self.assertNotIn(consultant_company, self.project.lead_consultant_companies)

        self.assertIn(consultant_company, self.project.regular_consultant_companies)
        self.assertNotIn(self.lead_consultant_company, self.project.regular_consultant_companies)

    def test_allocate_consultant_views(self):
        """Verify ProjectAllocateConsultantView and ProjectConsultantRemoveView."""
        self.client.force_login(self.user)
        consultant_company = ClientFactory(
            name="Test Consultant Company",
            type=Company.Type.CONSULTANT,
        )
        consultant_company.users.add(self.user)

        # Test allocate view post
        url_allocate = reverse(
            "client:project-lead-consultant:project-consultant-allocate",
            kwargs={"project_pk": self.project.pk},
        )
        response = self.client.post(url_allocate, {
            "consultant": consultant_company.pk,
            "type": Company.Type.CONSULTANT,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.project.consultants.filter(pk=consultant_company.pk).exists())

        # Test remove view post
        url_remove = reverse(
            "client:project-lead-consultant:project-consultant-remove",
            kwargs={"project_pk": self.project.pk, "consultant_pk": consultant_company.pk},
        )
        response = self.client.post(url_remove)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.project.consultants.filter(pk=consultant_company.pk).exists())

    def test_allocate_lead_consultant_views(self):
        """Verify ProjectAllocateLeadConsultantView and ProjectLeadConsultantRemoveView."""
        self.client.force_login(self.user)
        lead_consultant = ClientFactory(
            name="Test Lead Consultant Company 2",
            type=Company.Type.LEAD_CONSULTANT,
        )
        lead_consultant.users.add(self.user)

        # Test allocate view post
        url_allocate = reverse(
            "client:project-lead-consultant:project-lead-consultant-allocate",
            kwargs={"project_pk": self.project.pk},
        )
        response = self.client.post(url_allocate, {
            "lead_consultant": lead_consultant.pk,
            "type": Company.Type.LEAD_CONSULTANT,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.project.consultants.filter(pk=lead_consultant.pk).exists())

        # Test remove view post
        url_remove = reverse(
            "client:project-lead-consultant:project-lead-consultant-remove",
            kwargs={"project_pk": self.project.pk, "lead_consultant_pk": lead_consultant.pk},
        )
        response = self.client.post(url_remove)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.project.consultants.filter(pk=lead_consultant.pk).exists())

    def test_allocate_consultant_updates_type(self):
        """Verify allocating a consultant updates their type contextually."""
        self.client.force_login(self.user)

        # Start as LEAD_CONSULTANT
        company = ClientFactory(
            name="Flexible Consultant",
            type=Company.Type.LEAD_CONSULTANT,
        )
        company.users.add(self.user)

        # Allocate as regular CONSULTANT
        url_allocate = reverse(
            "client:project-lead-consultant:project-consultant-allocate",
            kwargs={"project_pk": self.project.pk},
        )
        self.client.post(url_allocate, {
            "consultant": company.pk,
            "type": Company.Type.CONSULTANT,
        })

        # Verify type has changed to CONSULTANT
        company.refresh_from_db()
        self.assertEqual(company.type, Company.Type.CONSULTANT)

    def test_allocate_lead_consultant_updates_type(self):
        """Verify allocating a lead consultant updates their type contextually."""
        self.client.force_login(self.user)

        # Start as regular CONSULTANT
        company = ClientFactory(
            name="Flexible Lead Consultant",
            type=Company.Type.CONSULTANT,
        )
        company.users.add(self.user)

        # Allocate as LEAD_CONSULTANT
        url_allocate = reverse(
            "client:project-lead-consultant:project-lead-consultant-allocate",
            kwargs={"project_pk": self.project.pk},
        )
        self.client.post(url_allocate, {
            "lead_consultant": company.pk,
            "type": Company.Type.LEAD_CONSULTANT,
        })

        # Verify type has changed to LEAD_CONSULTANT
        company.refresh_from_db()
        self.assertEqual(company.type, Company.Type.LEAD_CONSULTANT)

    def test_create_consultant_associates_creator_user(self):
        """Verify creating a company via LeadConsultantCreateView associates the current user."""
        self.client.force_login(self.user)

        url_create = reverse(
            "client:lead-consultant-management:lead-consultant-create",
            kwargs={"project_pk": self.project.pk},
        )
        response = self.client.post(url_create, {
            "name": "Self Created Consultant",
            "registration_number": "REG-SELF",
        })
        self.assertEqual(response.status_code, 302)

        company = Company.objects.get(name="Self Created Consultant")
        self.assertEqual(company.type, Company.Type.LEAD_CONSULTANT)
        self.assertIn(self.user, company.users.all())
        self.assertIn(self.user, company.consultants.all())


