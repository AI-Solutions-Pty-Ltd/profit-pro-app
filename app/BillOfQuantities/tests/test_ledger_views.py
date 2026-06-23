"""Tests for Ledger cancel_url and cert_id logic in views."""

import pytest
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import PaymentCertificate
from app.BillOfQuantities.tests.factories import PaymentCertificateFactory
from app.Project.models import Role
from app.Project.tests.factories import ProjectFactory, ProjectRoleFactory


@pytest.mark.django_db
class TestLedgerViewsCancelUrl:
    """Test cancel_url and cert_id logic in ledger list views."""

    def test_cancel_url_with_query_param(self, client):
        """Should resolve cancel_url and cert_id from query parameter."""
        project = ProjectFactory()
        user = AccountFactory()
        ProjectRoleFactory(project=project, user=user, role=Role.USER)
        cert = PaymentCertificateFactory(
            project=project, status=PaymentCertificate.Status.DRAFT
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:advance-payment-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(f"{url}?certificate={cert.pk}")

        assert response.status_code == 200
        assert response.context["cert_id"] == str(cert.pk)
        assert response.context["cancel_url"] == reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )

    def test_cancel_url_fallback_to_draft(self, client):
        """Should fall back to active draft certificate if query param is absent."""
        project = ProjectFactory()
        user = AccountFactory()
        ProjectRoleFactory(project=project, user=user, role=Role.USER)
        cert = PaymentCertificateFactory(
            project=project, status=PaymentCertificate.Status.DRAFT
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:advance-payment-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["cert_id"] == cert.pk
        assert response.context["cancel_url"] == reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )

    def test_cancel_url_no_fallback_without_draft(self, client):
        """Should set cancel_url to None if query param is absent and no draft certificate exists."""
        project = ProjectFactory()
        user = AccountFactory()
        ProjectRoleFactory(project=project, user=user, role=Role.USER)
        # Payment certificate has APPROVED status (not DRAFT)
        PaymentCertificateFactory(
            project=project, status=PaymentCertificate.Status.APPROVED
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:advance-payment-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert (
            "cert_id" not in response.context or response.context.get("cert_id") is None
        )
        assert (
            "cancel_url" not in response.context
            or response.context.get("cancel_url") is None
        )
