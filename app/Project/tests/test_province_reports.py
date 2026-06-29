import pytest
from decimal import Decimal
from django.urls import reverse

from app.Project.tests.factories import AccountFactory, ProjectFactory
from app.Account.tests.factories import ProvinceFactory, MunicipalityFactory
from app.BillOfQuantities.tests.factories import PaymentCertificateFactory
from app.Project.models import Project
from app.BillOfQuantities.models.payment_certificate_models import PaymentCertificate


@pytest.mark.django_db
class TestProvinceReports:
    """Test cases for aggregated province-level reports."""

    def setup_method(self):
        # Create user and projects
        self.user = AccountFactory()
        
        # Create province and municipality
        self.province = ProvinceFactory(name="Gauteng", code="GP")
        self.municipality = MunicipalityFactory(province=self.province, municipality_name="Tshwane")
        
        # Create project linked to municipality
        self.project = ProjectFactory(
            name="School Project 1",
            area=self.municipality,
            status=Project.Status.ACTIVE,
            vat=True
        )
        self.project.users.add(self.user)
        
        # Create an approved payment certificate for the project
        self.cert = PaymentCertificateFactory(
            project=self.project,
            certificate_number=1,
            status="APPROVED"
        )

    def _apply_mocks(self, monkeypatch):
        # Mock Project properties
        monkeypatch.setattr(Project, "original_contract_value", property(lambda self: Decimal("100000.00")))
        monkeypatch.setattr(Project, "addendum_contract_value", property(lambda self: Decimal("20000.00")))
        monkeypatch.setattr(Project, "revised_contract_value", property(lambda self: Decimal("120000.00")))
        monkeypatch.setattr(Project, "total_contract_value", property(lambda self: Decimal("120000.00")))

        # Mock PaymentCertificate properties/methods
        monkeypatch.setattr(PaymentCertificate, "work_progressive_to_date", property(lambda self: Decimal("50000.00")))
        monkeypatch.setattr(PaymentCertificate, "work_progressive_previous", property(lambda self: Decimal("10000.00")))
        monkeypatch.setattr(PaymentCertificate, "contract_current_claim_total", property(lambda self: Decimal("40000.00")))
        monkeypatch.setattr(PaymentCertificate, "addendum_current_claim_total", property(lambda self: Decimal("0.00")))
        monkeypatch.setattr(PaymentCertificate, "progressive_to_date", property(lambda self: Decimal("50000.00")))
        monkeypatch.setattr(PaymentCertificate, "progressive_previous", property(lambda self: Decimal("10000.00")))
        monkeypatch.setattr(PaymentCertificate, "get_advance_payment_total", lambda self: Decimal("0.00"))
        monkeypatch.setattr(PaymentCertificate, "previous_advance_payment_total", property(lambda self: Decimal("0.00")))
        monkeypatch.setattr(PaymentCertificate, "get_retention_total", lambda self: Decimal("0.00"))
        monkeypatch.setattr(PaymentCertificate, "previous_retention_total", property(lambda self: Decimal("0.00")))
        monkeypatch.setattr(PaymentCertificate, "get_materials_on_site_total", lambda self: Decimal("0.00"))
        monkeypatch.setattr(PaymentCertificate, "previous_materials_on_site_total", property(lambda self: Decimal("0.00")))
        monkeypatch.setattr(PaymentCertificate, "get_special_item_totals_by_type", lambda self: {})
        monkeypatch.setattr(PaymentCertificate, "previous_special_item_totals_by_type", property(lambda self: {}))

    def test_portfolio_province_summary_view(self, client, monkeypatch):
        """Test the list view showing all provinces with active projects."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        url = reverse("project:portfolio-province-summary")
        response = client.get(url)
        assert response.status_code == 200
        assert "portfolio/reports/province_summary.html" in [t.name for t in response.templates]
        
        # Check context data
        data = response.context["province_data"]
        assert len(data) == 1
        assert data[0]["province"] == self.province
        assert data[0]["project_count"] == 1
        assert data[0]["certs_count"] == 1
        assert data[0]["total_contract_value"] == Decimal("120000.00")
        assert data[0]["total_certified_value"] == Decimal("50000.00")
        
        all_provinces = list(response.context["all_provinces"])
        assert self.province in all_provinces

    def test_province_cover_page_view(self, client, monkeypatch):
        """Test the aggregated cover page HTML view for a province."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        url = reverse("project:portfolio-province-cover-page", kwargs={"province_pk": self.province.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "portfolio/reports/province_cover_page.html" in [t.name for t in response.templates]
        
        # Verify cover page sections
        ordered_sections = response.context["ordered_sections"]
        assert len(ordered_sections) == 3
        assert ordered_sections[0]["title"] == "Province Details"
        assert ordered_sections[1]["title"] == "Contract Value"
        assert ordered_sections[2]["title"] == "Progressive Valuations"

    def test_province_valuation_summary_view(self, client, monkeypatch):
        """Test the aggregated valuation summary HTML view for a province."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        url = reverse("project:portfolio-province-valuation-summary", kwargs={"province_pk": self.province.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "portfolio/reports/province_valuation_summary.html" in [t.name for t in response.templates]
        
        # Verify table calculations
        assert response.context["total_budget"] == Decimal("100000.00")
        assert response.context["total_variations"] == Decimal("20000.00")
        assert response.context["total_revised"] == Decimal("120000.00")
        assert response.context["total_previous"] == Decimal("10000.00")
        assert response.context["total_cumulative"] == Decimal("50000.00")
        assert response.context["total_current"] == Decimal("40000.00")

    def test_province_cover_page_xlsx_download(self, client, monkeypatch):
        """Test downloading the aggregated cover page as XLSX."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        url = reverse("project:portfolio-province-cover-page-xlsx", kwargs={"province_pk": self.province.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert f"province_{self.province.name.lower()}_cover_page.xlsx" in response["Content-Disposition"]

    def test_province_valuation_summary_xlsx_download(self, client, monkeypatch):
        """Test downloading the aggregated valuation summary as XLSX."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        url = reverse("project:portfolio-province-valuation-summary-xlsx", kwargs={"province_pk": self.province.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert f"province_{self.province.name.lower()}_valuation_summary.xlsx" in response["Content-Disposition"]
