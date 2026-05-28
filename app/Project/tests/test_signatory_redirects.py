"""Tests for Signatory Views success redirects and cancellations."""

import pytest
from django.test import Client
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Project.models import Signatories
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestSignatoryRedirects:
    """Test cases to verify that all signatory actions redirect back to the setup page."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Set up standard pytest client, user, and project with signatory role permissions."""
        self.client = Client()
        self.user = AccountFactory()
        self.project = ProjectFactory(users=[self.user])
        self.client.force_login(self.user)

    def test_signatory_invite_success_redirects_to_setup(self):
        """Verify that successfully inviting a signatory redirects the user to the setup page."""
        url = reverse(
            "project:signatory-invite", kwargs={"project_pk": self.project.pk}
        )
        post_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com",
            "primary_contact": "+27821112222",
            "sequence_number": 1,
            "role": "Signatory",
        }

        # Post valid form data
        response = self.client.post(url, post_data)

        # Check standard 302 redirect back to the project setup page
        assert response.status_code == 302
        expected_url = reverse("project:project-setup", kwargs={"pk": self.project.pk})
        assert response.url == expected_url

        # Verify signatory was actually created
        assert Signatories.objects.filter(
            project=self.project, user__email="johndoe@example.com"
        ).exists()

    def test_signatory_update_success_redirects_to_setup(self):
        """Verify that successfully updating a signatory redirects the user to the setup page."""
        # Create an existing signatory record
        signatory_user = AccountFactory(email="existing_signatory@example.com")
        signatory = Signatories.objects.create(
            project=self.project,
            user=signatory_user,
            sequence_number=1,
            role="Signatory",
        )

        url = reverse(
            "project:signatory-update",
            kwargs={"project_pk": self.project.pk, "pk": signatory.pk},
        )
        post_data = {
            "sequence_number": 2,
            "role": "Lead Signatory",
        }

        response = self.client.post(url, post_data)
        assert response.status_code == 302
        expected_url = reverse("project:project-setup", kwargs={"pk": self.project.pk})
        assert response.url == expected_url

        # Verify updated data
        signatory.refresh_from_db()
        assert signatory.sequence_number == 2
        assert signatory.role == "Lead Signatory"

    def test_signatory_delete_success_redirects_to_setup(self):
        """Verify that successfully deleting (removing) a signatory redirects to the setup page."""
        signatory_user = AccountFactory()
        signatory = Signatories.objects.create(
            project=self.project,
            user=signatory_user,
            sequence_number=1,
            role="Signatory",
        )

        url = reverse(
            "project:signatory-delete",
            kwargs={"project_pk": self.project.pk, "pk": signatory.pk},
        )

        # Delete view requires a POST confirm
        response = self.client.post(url)
        assert response.status_code == 302
        expected_url = reverse("project:project-setup", kwargs={"pk": self.project.pk})
        assert response.url == expected_url

        # Verify soft delete
        deleted_signatory = Signatories.all_objects.get(pk=signatory.pk)
        assert deleted_signatory.deleted is True

    def test_signatory_link_success_redirects_to_setup(self):
        """Verify that successfully linking an existing signatory user redirects to the setup page."""
        other_user = AccountFactory(first_name="Alice", last_name="Smith")

        url = reverse("project:signatory-link", kwargs={"project_pk": self.project.pk})
        post_data = {
            "signatories": other_user.pk,
        }

        response = self.client.post(url, post_data)
        assert response.status_code == 302
        expected_url = reverse("project:project-setup", kwargs={"pk": self.project.pk})
        assert response.url == expected_url

        # Verify linked
        assert Signatories.objects.filter(
            project=self.project, user=other_user
        ).exists()

    def test_signatory_resend_invite_redirects_to_setup(self):
        """Verify that resending an invitation email redirects back to the setup page."""
        signatory_user = AccountFactory()
        signatory = Signatories.objects.create(
            project=self.project,
            user=signatory_user,
            sequence_number=1,
            role="Signatory",
        )

        url = reverse(
            "project:signatory-resend-invite",
            kwargs={"project_pk": self.project.pk, "pk": signatory.pk},
        )

        response = self.client.get(url)
        assert response.status_code == 302
        expected_url = reverse("project:project-setup", kwargs={"pk": self.project.pk})
        assert response.url == expected_url
