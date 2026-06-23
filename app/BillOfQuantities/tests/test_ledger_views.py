"""Tests for ledger views."""

import pytest
from django.urls import reverse

from app.BillOfQuantities.tests.factories import (
    RetentionFactory,
)


@pytest.mark.django_db
class TestRetentionListView:
    """Test cases for RetentionListView."""

    def test_retention_list_view_success(self, client, user, project):
        """Test that the retention list view loads successfully."""
        # Create a retention transaction to ensure the list rendering logic runs
        RetentionFactory.create(project=project, captured_by=user)

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:retention-list", kwargs={"project_pk": project.pk}
        )

        # This GET request will render the template containing the broken URL reversal
        response = client.get(url)

        assert response.status_code == 200

    def test_retention_list_view_cancel_url(self, client, user, project):
        """Test that retention list view includes cancel_url when certificate is passed."""
        client.force_login(user)
        url = (
            reverse(
                "bill_of_quantities:retention-list", kwargs={"project_pk": project.pk}
            )
            + "?certificate=42"
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "cancel_url" in response.context
        assert "/payment-certificates/42/edit/" in response.context["cancel_url"]


@pytest.mark.django_db
class TestAdvancePaymentListView:
    """Test cases for AdvancePaymentListView."""

    def test_advance_payment_list_view_cancel_url(self, client, user, project):
        """Test that advance payment list view includes cancel_url when certificate is passed."""
        client.force_login(user)
        url = (
            reverse(
                "bill_of_quantities:advance-payment-list",
                kwargs={"project_pk": project.pk},
            )
            + "?certificate=42"
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "cancel_url" in response.context
        assert "/payment-certificates/42/edit/" in response.context["cancel_url"]


@pytest.mark.django_db
class TestMaterialsOnSiteListView:
    """Test cases for MaterialsOnSiteListView."""

    def test_materials_on_site_list_view_cancel_url(self, client, user, project):
        """Test that materials on site list view includes cancel_url when certificate is passed."""
        client.force_login(user)
        url = (
            reverse(
                "bill_of_quantities:materials-list", kwargs={"project_pk": project.pk}
            )
            + "?certificate=42"
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "cancel_url" in response.context
        assert "/payment-certificates/42/edit/" in response.context["cancel_url"]


@pytest.mark.django_db
class TestEscalationListView:
    """Test cases for EscalationListView."""

    def test_escalation_list_view_cancel_url(self, client, user, project):
        """Test that escalation list view includes cancel_url when certificate is passed."""
        client.force_login(user)
        url = (
            reverse(
                "bill_of_quantities:escalation-list", kwargs={"project_pk": project.pk}
            )
            + "?certificate=42"
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "cancel_url" in response.context
        assert "/payment-certificates/42/edit/" in response.context["cancel_url"]
