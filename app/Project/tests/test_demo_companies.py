"""Tests for seeding and conditional filtering of demo companies."""

from datetime import timedelta

import pytest
from django.utils import timezone

from app.Account.subscription_config import Subscription
from app.Account.tests.factories import AccountFactory
from app.Consultant.forms import ProjectClientForm
from app.Project.forms.forms import ProjectContractorForm, ProjectLeadConsultantForm
from app.Project.models import Company
from app.Project.projects.project_forms import ProjectFilterForm


@pytest.mark.django_db
class TestDemoCompaniesSeeding:
    """Test cases for seeding demo companies."""

    def test_ensure_demo_companies_creates_three_distinct_companies(self):
        """Test that calling ensure_demo_companies creates exactly three companies."""
        # Initial check
        assert Company.objects.filter(name__startswith="Demo").count() == 0

        # Seed companies
        demo_companies = Company.ensure_demo_companies()
        assert len(demo_companies) == 3

        # Verify correct types and names
        clients = Company.objects.filter(type=Company.Type.CLIENT, name="Demo Client")
        contractors = Company.objects.filter(
            type=Company.Type.CONTRACTOR, name="Demo Contractor 1"
        )
        consultants = Company.objects.filter(
            type=Company.Type.LEAD_CONSULTANT, name="Demo Consultant 1"
        )

        assert clients.exists()
        assert contractors.exists()
        assert consultants.exists()

    def test_ensure_demo_companies_idempotency(self):
        """Test that calling ensure_demo_companies multiple times is idempotent."""
        # First call
        Company.ensure_demo_companies()
        initial_count = Company.objects.filter(name__startswith="Demo").count()
        assert initial_count == 3

        # Second call
        Company.ensure_demo_companies()
        second_count = Company.objects.filter(name__startswith="Demo").count()
        assert second_count == 3  # No duplicates created


@pytest.mark.django_db
class TestDemoCompaniesFormFiltering:
    """Test cases for conditional filtering of demo companies in forms."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Set up necessary users and seed companies."""
        # Seed companies
        Company.ensure_demo_companies()

        # 1. Active trial demo user
        self.demo_user = AccountFactory.create(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=timezone.now() + timedelta(days=7),
        )

        # 2. Regular non-demo user
        self.regular_user = AccountFactory.create(
            subscription=Subscription.FREE_TIER,
            subscription_expires_at=timezone.now() + timedelta(days=30),
        )

        # 3. Expired trial demo user
        self.expired_demo_user = AccountFactory.create(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=timezone.now() - timedelta(days=1),
        )

    def test_project_client_form_filters_correctly(self):
        """Test that ProjectClientForm filters clients based on user demo permissions."""
        # Case A: Active demo user should see their own user-scoped Demo Client
        form_demo = ProjectClientForm(user=self.demo_user)
        queryset_demo = form_demo.fields["client"].queryset
        expected_name = f"{self.demo_user.first_name}'s Demo Client"
        assert queryset_demo.filter(name=expected_name).exists()
        assert not queryset_demo.filter(name="Demo Client").exists()

        # Case B: Regular user should NOT see Demo Client
        form_reg = ProjectClientForm(user=self.regular_user)
        queryset_reg = form_reg.fields["client"].queryset
        assert not queryset_reg.filter(name__contains="Demo Client").exists()

        # Case C: Expired demo user should NOT see Demo Client
        form_exp = ProjectClientForm(user=self.expired_demo_user)
        queryset_exp = form_exp.fields["client"].queryset
        assert not queryset_exp.filter(name__contains="Demo Client").exists()

    def test_project_contractor_form_filters_correctly(self):
        """Test that ProjectContractorForm filters contractors based on user demo permissions."""
        # Case A: Active demo user should see their own Demo Contractor 1
        form_demo = ProjectContractorForm(user=self.demo_user)
        queryset_demo = form_demo.fields["contractor"].queryset
        expected_name = f"{self.demo_user.first_name}'s Demo Contractor 1"
        assert queryset_demo.filter(name=expected_name).exists()

        # Case B: Regular user should NOT see Demo Contractor 1
        form_reg = ProjectContractorForm(user=self.regular_user)
        queryset_reg = form_reg.fields["contractor"].queryset
        assert not queryset_reg.filter(name__contains="Demo Contractor 1").exists()

        # Case C: Expired demo user should NOT see Demo Contractor 1
        form_exp = ProjectContractorForm(user=self.expired_demo_user)
        queryset_exp = form_exp.fields["contractor"].queryset
        assert not queryset_exp.filter(name__contains="Demo Contractor 1").exists()

    def test_project_lead_consultant_form_filters_correctly(self):
        """Test that ProjectLeadConsultantForm filters consultants based on user demo permissions."""
        # Case A: Active demo user should see their own Demo Consultant 1
        form_demo = ProjectLeadConsultantForm(user=self.demo_user)
        queryset_demo = form_demo.fields["lead_consultant"].queryset
        expected_name = f"{self.demo_user.first_name}'s Demo Consultant 1"
        assert queryset_demo.filter(name=expected_name).exists()

        # Case B: Regular user should NOT see Demo Consultant 1
        form_reg = ProjectLeadConsultantForm(user=self.regular_user)
        queryset_reg = form_reg.fields["lead_consultant"].queryset
        assert not queryset_reg.filter(name__contains="Demo Consultant 1").exists()

        # Case C: Expired demo user should NOT see Demo Consultant 1
        form_exp = ProjectLeadConsultantForm(user=self.expired_demo_user)
        queryset_exp = form_exp.fields["lead_consultant"].queryset
        assert not queryset_exp.filter(name__contains="Demo Consultant 1").exists()

    def test_project_filter_form_filters_correctly(self):
        """Test that ProjectFilterForm includes demo companies based on user demo permissions."""
        # Create standard/regular client and contractor companies (not demo companies)
        # Set created_by=self.demo_user for regular_client so Case A sees it
        regular_client = Company.objects.create(
            type=Company.Type.CLIENT,
            name="Regular Client",
            registration_number="REG-CLIENT",
            created_by=self.demo_user,
        )
        regular_contractor = Company.objects.create(
            type=Company.Type.CONTRACTOR,
            name="Regular Contractor",
            registration_number="REG-CONTRACTOR",
        )
        # Create a client company created by self.regular_user so Case B can see it
        regular_user_client = Company.objects.create(
            type=Company.Type.CLIENT,
            name="Regular User's Client",
            registration_number="REG-USER-CLIENT",
            created_by=self.regular_user,
        )

        # Mock/simulate the view-level queryset containing the user's projects' companies
        client_qs = Company.objects.filter(
            pk__in=[regular_client.pk, regular_user_client.pk]
        )
        contractor_qs = Company.objects.filter(pk=regular_contractor.pk)

        # Case A: Active demo user should see both standard (if created by them) and demo companies in ProjectFilterForm
        form_demo = ProjectFilterForm(
            user=self.demo_user,
            client_queryset=client_qs,
            contractor_queryset=contractor_qs,
        )
        expected_client = f"{self.demo_user.first_name}'s Demo Client"
        expected_contractor = f"{self.demo_user.first_name}'s Demo Contractor 1"
        assert form_demo.fields["client"].queryset.filter(name=expected_client).exists()
        assert (
            form_demo.fields["client"].queryset.filter(name="Regular Client").exists()
        )
        assert (
            not form_demo.fields["client"]
            .queryset.filter(name="Regular User's Client")
            .exists()
        )
        assert (
            form_demo.fields["contractor"]
            .queryset.filter(name=expected_contractor)
            .exists()
        )
        assert (
            form_demo.fields["contractor"]
            .queryset.filter(name="Regular Contractor")
            .exists()
        )
        assert (
            not form_demo.fields["client"].queryset.filter(name="Demo Client").exists()
        )

        # Case B: Regular user should see standard companies they created, but NOT demo companies
        form_reg = ProjectFilterForm(
            user=self.regular_user,
            client_queryset=client_qs,
            contractor_queryset=contractor_qs,
        )
        assert (
            not form_reg.fields["client"]
            .queryset.filter(name__contains="Demo Client")
            .exists()
        )
        assert (
            form_reg.fields["client"]
            .queryset.filter(name="Regular User's Client")
            .exists()
        )
        assert (
            not form_reg.fields["client"]
            .queryset.filter(name="Regular Client")
            .exists()
        )
        assert (
            not form_reg.fields["contractor"]
            .queryset.filter(name__contains="Demo Contractor 1")
            .exists()
        )
        assert (
            form_reg.fields["contractor"]
            .queryset.filter(name="Regular Contractor")
            .exists()
        )

        # Case C: Expired demo user should see standard companies they created, but NOT demo companies
        form_exp = ProjectFilterForm(
            user=self.expired_demo_user,
            client_queryset=client_qs,
            contractor_queryset=contractor_qs,
        )
        assert (
            not form_exp.fields["client"]
            .queryset.filter(name__contains="Demo Client")
            .exists()
        )
        assert (
            not form_exp.fields["client"]
            .queryset.filter(name="Regular Client")
            .exists()
        )
        assert (
            not form_exp.fields["contractor"]
            .queryset.filter(name__contains="Demo Contractor 1")
            .exists()
        )
        assert (
            form_exp.fields["contractor"]
            .queryset.filter(name="Regular Contractor")
            .exists()
        )

    def test_explicit_association_does_not_make_company_visible_to_non_creator(self):
        """Test that explicit association does not make a company visible to non-superusers who are not the creator."""
        # Get target demo client
        demo_client = Company.objects.get(name="Demo Client")

        # Explicitly associate the regular user with the Demo Client
        demo_client.users.add(self.regular_user)

        # Regular user should still NOT see the Demo Client because they are not the creator
        form_reg = ProjectClientForm(user=self.regular_user)
        queryset_reg = form_reg.fields["client"].queryset
        assert not queryset_reg.filter(name="Demo Client").exists()
