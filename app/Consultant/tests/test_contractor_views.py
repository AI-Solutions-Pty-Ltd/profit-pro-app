"""Test cases for contractor list view exclude logic."""

from typing import cast

from django.test import RequestFactory, TestCase

from app.Account.models import Account
from app.Account.tests.factories import AccountFactory
from app.Consultant.views.contractor_management_views import ContractorListView
from app.Project.models import Company, Project
from app.Project.tests.factories import ClientFactory, ProjectFactory


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

    def test_queryset_includes_unassigned_contractor_associated_with_user(self):
        """Test that the queryset includes a contractor associated with the user but not assigned to any project."""
        unassigned_contractor = ClientFactory(
            name="Unassigned Associated Contractor",
            type=Company.Type.CONTRACTOR,
        )
        unassigned_contractor.users.add(self.user)

        view = ContractorListView()
        request = self.factory.get("/")
        request.user = self.user
        view.request = request
        view.kwargs = {"project_pk": self.project.pk}

        # Initialize the project through the mixin
        view.project = self.project

        queryset = view.get_queryset()

        # Should return 3 contractors (contractor2, contractor3, and the unassigned associated contractor)
        self.assertEqual(queryset.count(), 3)
        self.assertIn(unassigned_contractor, queryset)


class TestRevealContractorFieldView(TestCase):
    """Test cases for RevealContractorFieldView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory()
        self.other_user = AccountFactory()

        from app.Project.models import Company, ProjectRole, Role

        self.contractor = ClientFactory(
            name="Test Contractor",
            type=Company.Type.CONTRACTOR,
            registration_number="REG-123456",
        )

        self.project = ProjectFactory(
            name="Privacy Project",
        )
        self.project.contractor = self.contractor
        self.project.save()

        # Grant Role.ADMIN to the main test user
        ProjectRole.objects.create(
            project=self.project, user=self.user, role=Role.ADMIN
        )

    def test_reveal_endpoint_success_for_authorized_user(self):
        """Test that an authorized project admin can retrieve decrypted values."""
        import json

        from django.urls import reverse

        self.client.force_login(self.user)

        url = reverse(
            "client:contractor-management:contractor-reveal-field",
            kwargs={"project_pk": self.project.pk, "company_pk": self.contractor.pk},
        )

        response = self.client.post(
            url,
            data=json.dumps({"field_name": "registration_number"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["value"], "REG-123456")

    def test_reveal_endpoint_forbidden_for_unauthorized_user(self):
        """Test that an unauthorized user receives 403 Forbidden."""
        import json

        from django.urls import reverse

        self.client.force_login(self.other_user)

        url = reverse(
            "client:contractor-management:contractor-reveal-field",
            kwargs={"project_pk": self.project.pk, "company_pk": self.contractor.pk},
        )

        response = self.client.post(
            url,
            data=json.dumps({"field_name": "registration_number"}),
            content_type="application/json",
        )
        # ContractorMixin enforces Role.ADMIN or raises permission error / 403
        self.assertEqual(response.status_code, 403)

    def test_reveal_endpoint_bad_request_for_invalid_field(self):
        """Test that requesting an invalid or non-sensitive field returns 400."""
        import json

        from django.urls import reverse

        self.client.force_login(self.user)

        url = reverse(
            "client:contractor-management:contractor-reveal-field",
            kwargs={"project_pk": self.project.pk, "company_pk": self.contractor.pk},
        )

        response = self.client.post(
            url,
            data=json.dumps({"field_name": "name"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class TestProjectContractorRemoveView(TestCase):
    """Test cases for ProjectContractorRemoveView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory()
        self.other_user = AccountFactory()

        from app.Project.models import Company, ProjectRole, Role

        self.contractor = ClientFactory(
            name="Contractor To Remove",
            type=Company.Type.CONTRACTOR,
        )

        self.project = ProjectFactory(
            name="Remove Project",
        )
        self.project.contractor = self.contractor
        self.project.save()

        # Grant Role.ADMIN to the main test user
        ProjectRole.objects.create(
            project=self.project, user=self.user, role=Role.ADMIN
        )

    def test_get_remove_confirmation_page(self):
        """Test that the remove confirmation page renders successfully with contractor_confirm_remove.html."""
        from django.urls import reverse

        self.client.force_login(self.user)

        url = reverse(
            "client:project-contractor:project-contractor-remove",
            kwargs={"project_pk": self.project.pk, "contractor_pk": self.contractor.pk},
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "contractor/contractor_confirm_remove.html")
        self.assertContains(response, "Remove Contractor from Project")
        self.assertContains(response, self.contractor.name)

    def test_post_remove_contractor_from_project(self):
        """Test that POSTing to the remove view unlinks the contractor and redirects."""
        from django.urls import reverse

        self.client.force_login(self.user)

        url = reverse(
            "client:project-contractor:project-contractor-remove",
            kwargs={"project_pk": self.project.pk, "contractor_pk": self.contractor.pk},
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # Refresh project from DB
        self.project.refresh_from_db()
        self.assertIsNone(self.project.contractor)

        # Should redirect to contractor-list
        list_url = reverse(
            "client:contractor-management:contractor-list",
            kwargs={"project_pk": self.project.pk},
        )
        self.assertRedirects(response, list_url)

