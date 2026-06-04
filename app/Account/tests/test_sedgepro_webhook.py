"""Tests for SedgePro user invitation webhook endpoint."""

import pytest
from django.conf import settings
from django.contrib.auth.models import Group
from django.core import mail
from django.urls import reverse

from app.Account.models import Account
from app.Account.tests.factories import AccountFactory
from app.Project.tests.factories import ClientFactory

pytestmark = pytest.mark.django_db


class TestSedgeProWebhookView:
    """Test cases for SedgeProWebhookView."""

    def setup_method(self):
        """Set up testing context."""
        # Create a client company with a specific registration number
        self.company = ClientFactory.create(registration_number="SEDGE-REF-12345")
        self.url = reverse("users:auth:sedgepro_webhook")
        self.api_key = settings.SEDGEPRO_API_KEY
        self.headers = {"HTTP_X_SEDGEPRO_API_KEY": self.api_key}

    def test_webhook_unauthorized_missing_header(self, client):
        """Test that requests without the API key header return 401."""
        response = client.post(
            self.url,
            {"email": "test@example.com", "client_reference": "SEDGE-REF-12345"},
            content_type="application/json",
        )
        assert response.status_code == 401
        assert response.json() == {"error": "Unauthorized"}

    def test_webhook_unauthorized_invalid_key(self, client):
        """Test that requests with an invalid API key return 401."""
        response = client.post(
            self.url,
            {"email": "test@example.com", "client_reference": "SEDGE-REF-12345"},
            content_type="application/json",
            HTTP_X_SEDGEPRO_API_KEY="invalid-key-123",
        )
        assert response.status_code == 401
        assert response.json() == {"error": "Unauthorized"}

    def test_webhook_invalid_json(self, client):
        """Test that malformed JSON payloads return 400."""
        response = client.post(
            self.url,
            "invalid-json-payload",
            content_type="application/json",
            **self.headers,
        )
        assert response.status_code == 400
        assert "error" in response.json()

    def test_webhook_missing_required_fields(self, client):
        """Test that requests missing email or client_reference return 400."""
        response = client.post(
            self.url,
            {"email": "test@example.com"},
            content_type="application/json",
            **self.headers,
        )
        assert response.status_code == 400
        assert "error" in response.json()

    def test_webhook_company_not_found(self, client):
        """Test that an unrecognized client reference returns 400."""
        response = client.post(
            self.url,
            {"email": "test@example.com", "client_reference": "NON-EXISTENT-REF"},
            content_type="application/json",
            **self.headers,
        )
        assert response.status_code == 400
        assert response.json() == {"error": "Company not found"}

    def test_webhook_success_new_user(self, client):
        """Test inviting a brand new user is successful."""
        email = "newinvitee@example.com"
        first_name = "Jane"
        last_name = "Smith"
        primary_contact = "+27821234567"

        # Ensure user does not exist
        assert not Account.objects.filter(email=email).exists()
        mail.outbox.clear()

        payload = {
            "email": email,
            "client_reference": "SEDGE-REF-12345",
            "first_name": first_name,
            "last_name": last_name,
            "primary_contact": primary_contact,
        }

        response = client.post(
            self.url, payload, content_type="application/json", **self.headers
        )

        assert response.status_code == 200
        assert response.json() == {"status": "success", "message": "User invited"}

        # Verify user created with correct details
        user = Account.objects.get(email=email)
        assert user.first_name == first_name
        assert user.last_name == last_name
        assert str(user.primary_contact) == "082 123 4567"
        assert user.type == Account.Type.CLIENT
        assert not user.has_usable_password()

        # Verify associated with company
        assert self.company.users.filter(pk=user.pk).exists()

        # Verify added to consultant group
        consultant_group = Group.objects.get(name="consultant")
        assert user.groups.filter(pk=consultant_group.pk).exists()

        # Verify email sent
        if settings.USE_EMAIL:
            assert len(mail.outbox) == 1
            assert "invited" in mail.outbox[0].subject

    def test_webhook_success_existing_user_not_linked(self, client):
        """Test inviting an existing user who is not currently associated with the client."""
        # Create existing user
        user = AccountFactory.create(email="existing@example.com")
        assert not self.company.users.filter(pk=user.pk).exists()
        mail.outbox.clear()

        payload = {
            "email": user.email,
            "client_reference": "SEDGE-REF-12345",
        }

        response = client.post(
            self.url, payload, content_type="application/json", **self.headers
        )

        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "User linked to company",
        }

        # Verify associated with company
        assert self.company.users.filter(pk=user.pk).exists()

        # Verify added to consultant group
        consultant_group = Group.objects.get(name="consultant")
        assert user.groups.filter(pk=consultant_group.pk).exists()

        # Verify email sent
        if settings.USE_EMAIL:
            assert len(mail.outbox) == 1
            assert "added" in mail.outbox[0].subject

    def test_webhook_success_existing_user_already_linked(self, client):
        """Test inviting an existing user who is already associated with the client (idempotency)."""
        # Create existing user and associate with company
        user = AccountFactory.create(email="already-linked@example.com")
        self.company.users.add(user)
        assert self.company.users.filter(pk=user.pk).exists()
        mail.outbox.clear()

        payload = {
            "email": user.email,
            "client_reference": "SEDGE-REF-12345",
        }

        response = client.post(
            self.url, payload, content_type="application/json", **self.headers
        )

        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "User already associated with company",
        }

        # Verify email was NOT sent
        assert len(mail.outbox) == 0

    def test_webhook_supabase_wrapper_format(self, client):
        """Test that payloads wrapped inside Supabase's database webhook envelopes are processed correctly."""
        email = "supabase-user@example.com"
        first_name = "Jane"
        last_name = "Smith"

        assert not Account.objects.filter(email=email).exists()

        # Envelop payload in standard Supabase record structure
        supabase_envelope = {
            "type": "INSERT",
            "table": "payments",
            "schema": "public",
            "record": {
                "user_email": email,
                "client_reference": "SEDGE-REF-12345",
                "first_name": first_name,
                "last_name": last_name,
            },
            "old_record": None,
        }

        response = client.post(
            self.url,
            supabase_envelope,
            content_type="application/json",
            **self.headers,
        )

        assert response.status_code == 200
        assert response.json() == {"status": "success", "message": "User invited"}

        # Verify user created
        user = Account.objects.get(email=email)
        assert user.first_name == first_name
        assert user.last_name == last_name
        assert self.company.users.filter(pk=user.pk).exists()
