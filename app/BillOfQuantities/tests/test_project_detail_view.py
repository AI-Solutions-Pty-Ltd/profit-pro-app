"""Tests for project detail payment certificate view."""

import pytest
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import PaymentCertificate
from app.BillOfQuantities.tests.factories import PaymentCertificateFactory
from app.Project.tests.factories import ProjectFactory


class TestProjectPaymentCertificateDetailView:
    """Test cases for ProjectPaymentCertificateDetailView."""

    @pytest.fixture
    def user(self):
        return AccountFactory()

    @pytest.fixture
    def project(self, user):
        return ProjectFactory(users=user)

    @pytest.fixture
    def certificate(self, project):
        return PaymentCertificateFactory(project=project)

    def test_view_requires_login(self, client, certificate):
        """Test that view requires login."""
        url = reverse(
            "bill_of_quantities:payment-certificate-detail",
            kwargs={"pk": certificate.pk, "project_pk": certificate.project.pk},
        )
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_view_shows_no_certificates(self, client, user, project):
        """Test view shows no certificates message."""
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "No Active Certificate" in response.content.decode()

    def test_view_shows_active_certificate(self, client, user, project, certificate):
        """Test view shows active certificate."""
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-detail",
            kwargs={"pk": certificate.pk, "project_pk": certificate.project.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert (
            f"Certificate: #{certificate.certificate_number}"
            in response.content.decode()
        )

    def test_view_shows_completed_certificates(self, client, user, project):
        """Test view shows completed certificates with totals."""
        client.force_login(user)
        _certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.APPROVED
        )
        url = reverse(
            "bill_of_quantities:payment-certificate-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "Completed Payment Certificates" in response.content.decode()

    def test_view_shows_correct_project(self, client, user, project):
        """Test view only shows certificates for correct project."""
        client.force_login(user)
        other_project = ProjectFactory(account=user)
        PaymentCertificateFactory.create(
            project=other_project, status=PaymentCertificate.Status.SUBMITTED
        )

        url = reverse(
            "bill_of_quantities:payment-certificate-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "No Active Certificate" in response.content.decode()

    def test_user_can_only_see_own_projects(self, client, user):
        """Test user can only see their own projects."""
        other_user = AccountFactory.create()
        other_project = ProjectFactory.create(users=other_user)

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-list",
            kwargs={"project_pk": other_project.pk},
        )
        response = client.get(url)
        assert response.status_code == 404
