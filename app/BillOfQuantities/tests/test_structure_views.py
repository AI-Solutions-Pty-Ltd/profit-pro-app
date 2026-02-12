"""Tests for Structure views."""

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import Structure
from app.BillOfQuantities.tests.factories import StructureFactory
from app.Project.models import ProjectRole, Role
from app.Project.tests.factories import ProjectFactory


class TestStructureListView(TestCase):
    """Test cases for StructureListView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create()
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        # Create test structures
        self.structure1 = StructureFactory.create(
            project=self.project, name="Section A"
        )
        self.structure2 = StructureFactory.create(
            project=self.project, name="Section B"
        )

        self.url = reverse(
            "bill_of_quantities:structure-list", kwargs={"project_pk": self.project.pk}
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible with correct permission."""
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_view_requires_permission(self):
        """Test view requires correct permission."""
        # Change role to one without permission
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        # Should redirect to login page when user doesn't have permission
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_view_shows_project_structures(self):
        """Test view shows structures for the correct project."""
        other_project = ProjectFactory.create()
        other_structure = StructureFactory.create(project=other_project)

        response = self.client.get(self.url)
        assert response.status_code == 200

        structures = response.context["structures"]
        assert self.structure1 in structures
        assert self.structure2 in structures
        assert other_structure not in structures

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_list.html")

    def test_context_data(self):
        """Test context data is correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.context["project"] == self.project

    def test_breadcrumbs(self):
        """Test breadcrumbs are correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["title"] == "Project Management"
        assert breadcrumbs[1]["title"] == "Sections"


class TestStructureDetailView(TestCase):
    """Test cases for StructureDetailView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create()
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        self.structure = StructureFactory.create(
            project=self.project, name="Test Section"
        )
        self.url = reverse(
            "bill_of_quantities:structure-detail",
            kwargs={"project_pk": self.project.pk, "pk": self.structure.pk},
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible with correct permission."""
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_view_requires_permission(self):
        """Test view requires correct permission."""
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        # Should redirect to login page when user doesn't have permission
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_detail.html")

    def test_context_data(self):
        """Test context data is correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.context["structure"] == self.structure
        assert response.context["project"] == self.project

    def test_breadcrumbs(self):
        """Test breadcrumbs are correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["title"] == "Sections"
        assert breadcrumbs[1]["title"] == self.structure.name


class TestStructureUpdateView(TestCase):
    """Test cases for StructureUpdateView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create()
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        self.structure = StructureFactory.create(
            project=self.project, name="Original Section"
        )
        self.url = reverse(
            "bill_of_quantities:structure-update",
            kwargs={"project_pk": self.project.pk, "pk": self.structure.pk},
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible with correct permission."""
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_view_requires_permission(self):
        """Test view requires correct permission."""
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        # Should redirect to login page when user doesn't have permission
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_form.html")

    def test_form_submission_success(self):
        """Test successful form submission."""
        data = {"name": "Updated Section", "description": "Updated description"}
        response = self.client.post(self.url, data)
        assert response.status_code == 302

        # Check object was updated
        self.structure.refresh_from_db()
        assert self.structure.name == "Updated Section"
        assert self.structure.description == "Updated description"

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "Section 'Updated Section' updated successfully!" in str(messages[0])

    def test_success_url(self):
        """Test successful redirect URL."""
        data = {"name": "Updated Section", "description": "Test"}
        response = self.client.post(self.url, data)
        assert response.status_code == 302
        expected_url = reverse(
            "bill_of_quantities:structure-list", kwargs={"project_pk": self.project.pk}
        )
        assert response["Location"] == expected_url

    def test_breadcrumbs(self):
        """Test breadcrumbs are correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["title"] == "Sections"
        assert "Edit" in breadcrumbs[1]["title"]


class TestStructureDeleteView(TestCase):
    """Test cases for StructureDeleteView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create()
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        self.structure = StructureFactory.create(
            project=self.project, name="Section to Delete"
        )
        self.url = reverse(
            "bill_of_quantities:structure-delete",
            kwargs={"project_pk": self.project.pk, "pk": self.structure.pk},
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible with correct permission."""
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_view_requires_permission(self):
        """Test view requires correct permission."""
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        # Should redirect to login page when user doesn't have permission
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_confirm_delete.html")

    def test_deletion_success(self):
        """Test successful deletion."""
        response = self.client.post(self.url)
        assert response.status_code == 302

        # Check object was soft deleted
        try:
            self.structure.refresh_from_db()
            assert self.structure.is_deleted is True
        except Structure.DoesNotExist:
            # Object was actually deleted from database
            pass

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "Section 'Section to Delete' deleted successfully!" in str(messages[0])

    def test_success_url(self):
        """Test successful redirect URL."""
        response = self.client.post(self.url)
        assert response.status_code == 302
        expected_url = reverse(
            "bill_of_quantities:structure-list", kwargs={"project_pk": self.project.pk}
        )
        assert response["Location"] == expected_url

    def test_breadcrumbs(self):
        """Test breadcrumbs are correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["title"] == "Sections"
        assert "Delete" in breadcrumbs[1]["title"]


class TestStructureExcelUploadView(TestCase):
    """Test cases for StructureExcelUploadView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create()
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        self.url = reverse(
            "bill_of_quantities:structure-upload",
            kwargs={"project_pk": self.project.pk},
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible with correct permission."""
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_view_requires_permission(self):
        """Test view requires correct permission."""
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        # Should redirect to login page when user doesn't have permission
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_excel_upload.html")

    def test_context_data(self):
        """Test context data is correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.context["project"] == self.project

    def test_breadcrumbs(self):
        """Test breadcrumbs are correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["title"] == "Structures"
        assert breadcrumbs[1]["title"] == "Upload Structures"
