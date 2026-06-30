from decimal import Decimal

import pytest
from django.urls import reverse

from app.Account.tests.factories import MunicipalityFactory, ProvinceFactory
from app.BillOfQuantities.models.payment_certificate_models import PaymentCertificate
from app.BillOfQuantities.tests.factories import PaymentCertificateFactory
from app.Project.models import Project
from app.Project.tests.factories import AccountFactory, ProjectFactory


@pytest.mark.django_db
class TestMultiProjectReports:
    """Test cases for custom multi-project selected reports."""

    def setup_method(self):
        # Create user
        self.user = AccountFactory()

        # Create province and municipality
        self.province = ProvinceFactory(name="Gauteng", code="GP")
        self.municipality = MunicipalityFactory(
            province=self.province, municipality_name="Tshwane"
        )

        # Create two projects
        self.project1 = ProjectFactory(
            name="Multi School Project 1",
            area=self.municipality,
            status=Project.Status.ACTIVE,
            vat=True,
        )
        self.project2 = ProjectFactory(
            name="Multi Clinic Project 2",
            area=self.municipality,
            status=Project.Status.ACTIVE,
            vat=True,
        )
        self.project1.users.add(self.user)
        self.project2.users.add(self.user)

        # Create approved certificates for both
        self.cert1 = PaymentCertificateFactory(
            project=self.project1, certificate_number=1, status="APPROVED"
        )
        self.cert2 = PaymentCertificateFactory(
            project=self.project2, certificate_number=1, status="APPROVED"
        )
        self.project_ids_str = f"{self.project1.pk},{self.project2.pk}"

    def _apply_mocks(self, monkeypatch):
        # Mock Project properties
        monkeypatch.setattr(
            Project,
            "original_contract_value",
            property(lambda self: Decimal("100000.00")),
        )
        monkeypatch.setattr(
            Project,
            "addendum_contract_value",
            property(lambda self: Decimal("20000.00")),
        )
        monkeypatch.setattr(
            Project,
            "revised_contract_value",
            property(lambda self: Decimal("120000.00")),
        )
        monkeypatch.setattr(
            Project, "total_contract_value", property(lambda self: Decimal("120000.00"))
        )

        # Mock PaymentCertificate properties/methods
        monkeypatch.setattr(
            PaymentCertificate,
            "work_progressive_to_date",
            property(lambda self: Decimal("50000.00")),
        )
        monkeypatch.setattr(
            PaymentCertificate,
            "work_progressive_previous",
            property(lambda self: Decimal("10000.00")),
        )
        monkeypatch.setattr(
            PaymentCertificate,
            "contract_current_claim_total",
            property(lambda self: Decimal("40000.00")),
        )
        monkeypatch.setattr(
            PaymentCertificate,
            "addendum_current_claim_total",
            property(lambda self: Decimal("0.00")),
        )
        monkeypatch.setattr(
            PaymentCertificate,
            "progressive_to_date",
            property(lambda self: Decimal("50000.00")),
        )
        monkeypatch.setattr(
            PaymentCertificate,
            "progressive_previous",
            property(lambda self: Decimal("10000.00")),
        )

        monkeypatch.setattr(
            PaymentCertificate,
            "get_advance_payment_total",
            lambda self: Decimal("0.00"),
        )
        monkeypatch.setattr(
            PaymentCertificate,
            "previous_advance_payment_total",
            property(lambda self: Decimal("0.00")),
        )
        monkeypatch.setattr(
            PaymentCertificate, "get_retention_total", lambda self: Decimal("0.00")
        )
        monkeypatch.setattr(
            PaymentCertificate,
            "previous_retention_total",
            property(lambda self: Decimal("0.00")),
        )
        monkeypatch.setattr(
            PaymentCertificate,
            "get_materials_on_site_total",
            lambda self: Decimal("0.00"),
        )
        monkeypatch.setattr(
            PaymentCertificate,
            "previous_materials_on_site_total",
            property(lambda self: Decimal("0.00")),
        )
        monkeypatch.setattr(
            PaymentCertificate, "get_special_item_totals_by_type", lambda self: {}
        )
        monkeypatch.setattr(
            PaymentCertificate,
            "previous_special_item_totals_by_type",
            property(lambda self: {}),
        )

    def test_multi_project_cover_page_view(self, client, monkeypatch):
        """Test rendering the aggregated multi-project cover page."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        url = f"{reverse('project:portfolio-multi-cover-page')}?project_ids={self.project_ids_str}"
        response = client.get(url)
        assert response.status_code == 200
        assert "portfolio/reports/multi_project_cover_page.html" in [
            t.name for t in response.templates
        ]

        ordered_sections = response.context["ordered_sections"]
        assert len(ordered_sections) == 3
        assert ordered_sections[0]["title"] == "Selected Projects Details"
        assert ordered_sections[1]["title"] == "Contract Value"
        assert ordered_sections[2]["title"] == "Progressive Valuations"

    def test_multi_project_valuation_summary_view(self, client, monkeypatch):
        """Test rendering the aggregated multi-project valuation summary."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        url = f"{reverse('project:portfolio-multi-valuation-summary')}?project_ids={self.project_ids_str}"
        response = client.get(url)
        assert response.status_code == 200
        assert "portfolio/reports/multi_project_valuation_summary.html" in [
            t.name for t in response.templates
        ]

        # Verify sums in context (for two projects matched by mocks)
        assert response.context["total_budget"] == Decimal("200000.00")
        assert response.context["total_variations"] == Decimal("40000.00")
        assert response.context["total_revised"] == Decimal("240000.00")
        assert response.context["total_previous"] == Decimal("20000.00")
        assert response.context["total_cumulative"] == Decimal("100000.00")
        assert response.context["total_current"] == Decimal("80000.00")

    def test_multi_project_cover_page_xlsx_download(self, client, monkeypatch):
        """Test downloading the aggregated cover page as XLSX."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        url = f"{reverse('project:portfolio-multi-cover-page-xlsx')}?project_ids={self.project_ids_str}"
        response = client.get(url)
        assert response.status_code == 200
        assert (
            response["Content-Type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert "aggregated_cover_page.xlsx" in response["Content-Disposition"]

    def test_multi_project_valuation_summary_xlsx_download(self, client, monkeypatch):
        """Test downloading the aggregated valuation summary as XLSX."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        url = f"{reverse('project:portfolio-multi-valuation-summary-xlsx')}?project_ids={self.project_ids_str}"
        response = client.get(url)
        assert response.status_code == 200
        assert (
            response["Content-Type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert "aggregated_valuation_summary.xlsx" in response["Content-Disposition"]
