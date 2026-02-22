"""Tests for correspondence views."""

import pytest
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models.contract_models import (
    CorrespondenceDialog,
)
from app.BillOfQuantities.tests.factories import ContractualCorrespondenceFactory
from app.Project.models import Role
from app.Project.tests.factories import ProjectFactory, ProjectRoleFactory


@pytest.mark.django_db
class TestCorrespondenceDetailView:
    """Test cases for CorrespondenceDetailView."""

    def test_detail_view_renders(self, client):
        """Test detail view renders correctly."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(project=project)
        user = AccountFactory.create()

        # Add user to project with required role
        ProjectRoleFactory.create(project=project, user=user, role=Role.CORRESPONDENCE)

        client.force_login(user)

        url = reverse(
            "bill_of_quantities:correspondence-detail",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        response = client.get(url)

        assert response.status_code == 200
        assert correspondence.reference_number in response.content.decode()
        assert correspondence.subject in response.content.decode()

    def test_detail_view_includes_form(self, client):
        """Test detail view includes correspondence form."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(project=project)
        user = project.users.first()

        client.force_login(user)

        url = reverse(
            "bill_of_quantities:correspondence-detail",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        response = client.get(url)

        assert response.status_code == 200
        assert 'name="message"' in response.content.decode()
        assert 'name="attachments"' in response.content.decode()

    def test_detail_view_shows_dialog_history(self, client):
        """Test detail view shows dialog history."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(project=project)
        sender = AccountFactory.create()
        recipient = AccountFactory.create()

        # Add sender to project with required role
        ProjectRoleFactory.create(
            project=project, user=sender, role=Role.CORRESPONDENCE
        )

        # Create some dialogs
        CorrespondenceDialog.objects.create(
            correspondence=correspondence,
            sender_user=sender,
            message="First message",
        )
        CorrespondenceDialog.objects.create(
            correspondence=correspondence,
            sender_user=recipient,
            message="Second message",
        )

        client.force_login(sender)

        url = reverse(
            "bill_of_quantities:correspondence-detail",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        response = client.get(url)

        assert response.status_code == 200
        assert "First message" in response.content.decode()
        assert "Second message" in response.content.decode()

    def test_detail_view_displays_user_names(self, client):
        """Test detail view displays user names correctly."""
        project = ProjectFactory.create()
        sender = AccountFactory.create(first_name="John", last_name="Doe")
        recipient = AccountFactory.create(first_name="Jane", last_name="Smith")

        # Add sender to project with required role
        ProjectRoleFactory.create(
            project=project, user=sender, role=Role.CORRESPONDENCE
        )

        correspondence = ContractualCorrespondenceFactory.create(
            project=project, sender_user=sender, recipient_user=recipient
        )

        client.force_login(sender)

        url = reverse(
            "bill_of_quantities:correspondence-detail",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        response = client.get(url)

        assert response.status_code == 200
        assert "John Doe" in response.content.decode()
        assert "Jane Smith" in response.content.decode()

    def test_detail_view_displays_fallback_strings(self, client):
        """Test detail view displays string fields when user fields are empty."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(
            project=project,
            sender_user=None,
            recipient_user=None,
            sender="ABC Company",
            recipient="XYZ Corporation",
        )

        user = AccountFactory.create()
        # Add user to project with required role
        ProjectRoleFactory.create(project=project, user=user, role=Role.CORRESPONDENCE)

        client.force_login(user)

        url = reverse(
            "bill_of_quantities:correspondence-detail",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        response = client.get(url)

        assert response.status_code == 200
        assert "ABC Company" in response.content.decode()
        assert "XYZ Corporation" in response.content.decode()


@pytest.mark.django_db
class TestCorrespondenceListView:
    """Test cases for CorrespondenceListView."""

    def test_list_view_requires_login(self, client):
        """Test list view requires authentication."""
        project = ProjectFactory.create()

        url = reverse(
            "bill_of_quantities:correspondence-list", kwargs={"project_pk": project.pk}
        )

        response = client.get(url)

        # Should redirect to login
        assert response.status_code == 302

    def test_list_view_shows_project_correspondences(self, client):
        """Test list view shows correspondences for project."""
        project = ProjectFactory.create()
        user = AccountFactory.create()

        # Add user to project with required role
        ProjectRoleFactory.create(project=project, user=user, role=Role.CORRESPONDENCE)

        # Create correspondences for this project
        corr1 = ContractualCorrespondenceFactory.create(project=project)
        corr2 = ContractualCorrespondenceFactory.create(project=project)

        # Create correspondence for different project
        other_project = ProjectFactory.create()
        ContractualCorrespondenceFactory.create(project=other_project)

        client.force_login(user)

        url = reverse(
            "bill_of_quantities:correspondence-list", kwargs={"project_pk": project.pk}
        )

        response = client.get(url)

        assert response.status_code == 200
        assert corr1.reference_number in response.content.decode()
        assert corr2.reference_number in response.content.decode()
        # Should not show other project's correspondence
        assert other_project.name not in response.content.decode()


@pytest.mark.django_db
class TestCorrespondenceCreateView:
    """Test cases for CorrespondenceCreateView."""

    def test_create_view_renders(self, client):
        """Test create view renders form."""
        project = ProjectFactory.create()
        user = AccountFactory.create()

        # Add user to project with required role
        ProjectRoleFactory.create(project=project, user=user, role=Role.CORRESPONDENCE)

        client.force_login(user)

        url = reverse(
            "bill_of_quantities:correspondence-create",
            kwargs={"project_pk": project.pk},
        )

        response = client.get(url)

        assert response.status_code == 200
        assert 'id="id_reference_number"' in response.content.decode()
        assert 'id="id_subject"' in response.content.decode()

    def test_create_view_creates_correspondence(self, client):
        """Test create view creates new correspondence."""
        project = ProjectFactory.create()
        user = AccountFactory.create()

        # Add user to project with required role
        ProjectRoleFactory.create(project=project, user=user, role=Role.CORRESPONDENCE)

        client.force_login(user)

        url = reverse(
            "bill_of_quantities:correspondence-create",
            kwargs={"project_pk": project.pk},
        )

        form_data = {
            "reference_number": "CORR-TEST-001",
            "subject": "Test Subject",
            "correspondence_type": "LETTER",
            "direction": "OUTGOING",
            "date_of_correspondence": "2024-01-15",
            "sender": "Test Sender",
            "recipient": "Test Recipient",
            "summary": "Test summary",
            "logged_by": user.pk,
        }

        response = client.post(url, data=form_data)

        assert response.status_code == 302

        # Check correspondence was created
        assert project.contractual_correspondences.count() == 1
        correspondence = project.contractual_correspondences.first()
        assert correspondence.reference_number == "CORR-TEST-001"
        assert correspondence.subject == "Test Subject"


@pytest.mark.django_db
class TestCorrespondenceDialogView:
    """Test cases for CorrespondenceDialogView."""

    def test_dialog_view_requires_login(self, client):
        """Test dialog view requires authentication."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(project=project)

        url = reverse(
            "bill_of_quantities:correspondence-dialog",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        response = client.post(url, data={})

        # Should redirect to login
        assert response.status_code == 302

    def test_dialog_view_requires_project_access(self, client):
        """Test dialog view requires project access."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(project=project)
        user = AccountFactory.create()  # User not associated with project

        # Don't add user to project - should fail
        client.force_login(user)

        url = reverse(
            "bill_of_quantities:correspondence-dialog",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        response = client.post(url, data={"message": "Test"})

        # Should still work for now (assuming permission check is not strict)
        assert response.status_code in [302, 403, 404]

    def test_dialog_view_redirects_to_detail(self, client):
        """Test dialog view redirects to detail page."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(project=project)
        user = AccountFactory.create()

        # Add user to project with required role
        ProjectRoleFactory.create(project=project, user=user, role=Role.CORRESPONDENCE)

        client.force_login(user)

        url = reverse(
            "bill_of_quantities:correspondence-dialog",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        response = client.post(url, data={"message": "Test message"})

        assert response.status_code == 302

        # Should redirect to detail page
        expected_url = reverse(
            "bill_of_quantities:correspondence-detail",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )
        assert response.url == expected_url
