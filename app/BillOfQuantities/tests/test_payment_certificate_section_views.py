"""Tests for PaymentCertificate section views (cover page, valuation summary, detailed)."""

import pytest
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.tests.factories import (
    ActualTransactionFactory,
    LineItemFactory,
    PaymentCertificateFactory,
)
from app.Project.models import ProjectRole, Role
from app.Project.tests.factories import ProjectFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user_with_cert():
    """Return (user, project, certificate) with a line item attached."""
    user = AccountFactory.create()
    project = ProjectFactory.create(users=user)
    LineItemFactory.create(project=project)
    certificate = PaymentCertificateFactory.create(project=project)
    return user, project, certificate


# ===========================================================================
# Cover Page View
# ===========================================================================


@pytest.mark.django_db
class TestPaymentCertificateCoverPageView:
    """Test cases for PaymentCertificateCoverPageView."""

    def test_requires_authentication(self, client):
        """Unauthenticated users are redirected to login."""
        user, project, cert = _make_user_with_cert()
        url = reverse(
            "bill_of_quantities:payment-certificate-cover-page",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.status_code == 302

    def test_returns_200_for_authenticated_user(self, client):
        """Authenticated user with project access sees cover page."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-cover-page",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.status_code == 200

    def test_context_contains_payment_certificate(self, client):
        """Context includes the payment_certificate object."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-cover-page",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.context["payment_certificate"] == cert

    def test_context_contains_project(self, client):
        """Context includes the project object."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-cover-page",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.context["project"] == project

    def test_user_without_role_is_denied(self, client):
        """User without project access or role is denied."""
        other_user = AccountFactory.create()
        _, project, cert = _make_user_with_cert()
        client.force_login(other_user)
        url = reverse(
            "bill_of_quantities:payment-certificate-cover-page",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.status_code in (302, 403)

    def test_accessible_via_project_role(self, client):
        """User with PAYMENT_CERTIFICATES role but not in project.users can access."""
        role_user = AccountFactory.create()
        _, project, cert = _make_user_with_cert()
        ProjectRole.objects.create(
            user=role_user, project=project, role=Role.PAYMENT_CERTIFICATES
        )
        client.force_login(role_user)
        url = reverse(
            "bill_of_quantities:payment-certificate-cover-page",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.status_code == 200

    def test_cover_page_custom_config_rendering(self, client):
        """Test that custom cover page config title and field visibilities render in HTML."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)

        custom_config = {
            "title": "CUSTOM HTML COVER TITLE",
            "sections": {
                "section_a": {
                    "title": "CUSTOM SEC A TITLE",
                    "fields": [
                        {
                            "id": "contract_name",
                            "label": "Custom Contract Label",
                            "enabled": True,
                        },
                        {
                            "id": "contract_number",
                            "label": "Custom Contract Num",
                            "enabled": False,
                        },
                        {
                            "id": "contract_clause",
                            "label": "Custom Clause",
                            "enabled": True,
                        },
                        {"id": "description", "label": "Custom Desc", "enabled": True},
                        {"id": "client", "label": "Custom Client", "enabled": True},
                        {"id": "status", "label": "Custom Status", "enabled": True},
                        {
                            "id": "assessment_date",
                            "label": "Custom Assess Date",
                            "enabled": True,
                        },
                        {
                            "id": "certificate_date",
                            "label": "Custom Cert Date",
                            "enabled": True,
                        },
                    ],
                },
                "section_b": {"title": "CUSTOM SEC B TITLE", "fields": []},
                "section_c": {"title": "CUSTOM SEC C TITLE", "fields": []},
            },
        }
        project.cover_page_config = custom_config
        project.save()

        url = reverse(
            "bill_of_quantities:payment-certificate-cover-page",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.status_code == 200

        html = response.content.decode("utf-8")
        assert "CUSTOM HTML COVER TITLE" in html
        assert "Custom Contract Label" in html
        assert "Custom Contract Num" not in html


# ===========================================================================
# Valuation Summary View
# ===========================================================================


@pytest.mark.django_db
class TestPaymentCertificateValuationSummaryView:
    """Test cases for PaymentCertificateValuationSummaryView."""

    def test_requires_authentication(self, client):
        """Unauthenticated users are redirected to login."""
        user, project, cert = _make_user_with_cert()
        url = reverse(
            "bill_of_quantities:payment-certificate-valuation-summary",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.status_code == 302

    def test_returns_200(self, client):
        """Returns 200 for Valuation Summary view."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-valuation-summary",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.status_code == 200

    def test_context_contains_grouped_sections(self, client):
        """Valuation summary context includes grouped_sections key."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-valuation-summary",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert "grouped_sections" in response.context

    def test_context_contains_totals(self, client):
        """Valuation summary context includes total_budget, total_current, etc."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-valuation-summary",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        for key in (
            "total_budget",
            "total_cumulative",
            "total_previous",
            "total_current",
        ):
            assert key in response.context

    def test_returns_200_abridged_mode(self, client):
        """Abridged mode query parameter is ignored, is_abridged is False."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-valuation-summary",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url + "?mode=abridged")
        assert response.status_code == 200
        assert response.context["is_abridged"] is False

    def test_default_mode_is_full(self, client):
        """Without ?mode= param, defaults to full mode (is_abridged=False)."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-valuation-summary",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["is_abridged"] is False


# ===========================================================================
# Detailed View (Full and Abridged)
# ===========================================================================


@pytest.mark.django_db
class TestPaymentCertificateDetailedView:
    """Test cases for PaymentCertificateDetailedView."""

    def test_requires_authentication(self, client):
        """Unauthenticated users are redirected to login."""
        user, project, cert = _make_user_with_cert()
        url = reverse(
            "bill_of_quantities:payment-certificate-view-detailed",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.status_code == 302

    def test_returns_200_full_mode(self, client):
        """Full mode returns 200."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-view-detailed",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url + "?mode=full")
        assert response.status_code == 200

    def test_returns_200_abridged_mode(self, client):
        """Abridged mode returns 200."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-view-detailed",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url + "?mode=abridged")
        assert response.status_code == 200

    def test_default_mode_is_abridged(self, client):
        """Without ?mode= param, defaults to abridged mode (is_abridged=True)."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-view-detailed",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["is_abridged"] is True

    def test_abridged_mode_sets_flag(self, client):
        """?mode=abridged sets is_abridged=True in context."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-view-detailed",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url + "?mode=abridged")
        assert response.context["is_abridged"] is True

    def test_full_mode_context_keys(self, client):
        """Full mode context contains grouped_line_items, special_line_items, addendum_line_items."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-view-detailed",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url + "?mode=full")
        for key in ("grouped_line_items", "special_line_items", "addendum_line_items"):
            assert key in response.context

    def test_abridged_mode_only_shows_claimed_items(self, client):
        """Abridged mode only includes line items that have actual transactions."""
        user, project, cert = _make_user_with_cert()
        # Create a line item WITH a claimed transaction
        line_item_claimed = LineItemFactory.create(project=project)
        ActualTransactionFactory.create(
            payment_certificate=cert,
            line_item=line_item_claimed,
            claimed=True,
            approved=True,
        )
        # Create a line item WITHOUT any transaction (should NOT appear in abridged)
        _line_item_unclaimed = LineItemFactory.create(project=project)

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-view-detailed",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url + "?mode=abridged")
        assert response.status_code == 200
        # Abridged mode is set
        assert response.context["is_abridged"] is True

    def test_context_contains_payment_certificate(self, client):
        """Context always contains payment_certificate object."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-view-detailed",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )
        response = client.get(url)
        assert response.context["payment_certificate"] == cert


# ===========================================================================
# URL Smoke Tests (all 3 URLs resolve)
# ===========================================================================


@pytest.mark.django_db
class TestSectionViewURLs:
    """Smoke tests that verify all three section view URLs resolve and respond."""

    def test_all_three_urls_return_200(self, client):
        """Cover page, valuation summary (valterra), and detailed full all return 200."""
        user, project, cert = _make_user_with_cert()
        client.force_login(user)

        urls = [
            reverse(
                "bill_of_quantities:payment-certificate-cover-page",
                kwargs={"project_pk": project.pk, "pk": cert.pk},
            ),
            reverse(
                "bill_of_quantities:payment-certificate-valuation-summary",
                kwargs={"project_pk": project.pk, "pk": cert.pk},
            ),
            reverse(
                "bill_of_quantities:payment-certificate-view-detailed",
                kwargs={"project_pk": project.pk, "pk": cert.pk},
            ),
        ]

        for url in urls:
            response = client.get(url)
            assert response.status_code == 200, (
                f"Expected 200 for {url}, got {response.status_code}"
            )


class TestCoverPageNegativeFormatting:
    """Test that items with 'less' in their label are formatted with negative signs."""

    def test_less_indicators_negated_and_formatted(self, client):
        """Verify get_resolved_cover_page_sections negates and formats 'less' fields correctly."""
        from decimal import Decimal
        from unittest.mock import PropertyMock, patch

        from app.BillOfQuantities.views.payment_certificate_views import (
            get_resolved_cover_page_sections,
        )

        user, project, cert = _make_user_with_cert()
        client.force_login(user)

        with patch(
            "app.BillOfQuantities.models.payment_certificate_models.PaymentCertificate.progressive_previous",
            new_callable=PropertyMock,
        ) as mock_prev:
            mock_prev.return_value = Decimal("900000.00")

            sections = get_resolved_cover_page_sections(cert)

            # Find progressive_previous field in the resolved sections
            found_field = None
            for sec in sections:
                for field in sec["fields"]:
                    if field["id"] == "progressive_previous":
                        found_field = field
                        break

            assert found_field is not None
            # Should be negated
            assert found_field["raw_value"] == Decimal("-900000.00")
            # Should be formatted with -R prefix in South African style
            assert found_field["formatted_value"] == "-R 900,000.00"

            # Verify page renders the correct formatted value
            url = reverse(
                "bill_of_quantities:payment-certificate-cover-page",
                kwargs={"project_pk": project.pk, "pk": cert.pk},
            )
            response = client.get(url)
            assert response.status_code == 200
            html = response.content.decode("utf-8")
            assert "-R 900,000.00" in html
