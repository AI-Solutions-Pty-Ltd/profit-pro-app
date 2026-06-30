import pytest
import json
from decimal import Decimal
from django.urls import reverse

from app.Project.tests.factories import AccountFactory, ProjectFactory, ProjectGroupFactory
from app.Account.tests.factories import ProvinceFactory, MunicipalityFactory
from app.BillOfQuantities.tests.factories import PaymentCertificateFactory
from app.Project.models import Project, ProjectGroup
from app.BillOfQuantities.models.payment_certificate_models import PaymentCertificate


@pytest.mark.django_db
class TestProjectGroups:
    """Test suite for project grouping and regional reporting."""

    def setup_method(self):
        self.user = AccountFactory()
        self.province_gp = ProvinceFactory(name="Gauteng", code="GP")
        self.province_kzn = ProvinceFactory(name="KwaZulu-Natal", code="KZN")
        
        self.muni_gp = MunicipalityFactory(province=self.province_gp, municipality_name="Johannesburg")
        self.muni_kzn = MunicipalityFactory(province=self.province_kzn, municipality_name="Durban")

        self.project1 = ProjectFactory(
            name="GP School",
            area=self.muni_gp,
            status=Project.Status.ACTIVE,
            vat=True
        )
        self.project2 = ProjectFactory(
            name="KZN Clinic",
            area=self.muni_kzn,
            status=Project.Status.ACTIVE,
            vat=True
        )
        self.project1.users.add(self.user)
        self.project2.users.add(self.user)

        self.cert1 = PaymentCertificateFactory(
            project=self.project1,
            certificate_number=1,
            status="APPROVED"
        )
        self.cert2 = PaymentCertificateFactory(
            project=self.project2,
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

    def test_group_create_api(self, client):
        """Test creating a project group via AJAX POST."""
        client.force_login(self.user)
        url = reverse("project:portfolio-group-create")
        post_data = {
            "name": "My Favorites",
            "project_ids": f"{self.project1.pk},{self.project2.pk}"
        }
        response = client.post(url, data=json.dumps(post_data), content_type="application/json")
        assert response.status_code == 200
        
        group = ProjectGroup.objects.filter(user=self.user, name="My Favorites", deleted=False).first()
        assert group is not None
        assert group.projects.count() == 2

    def test_group_create_duplicate_api(self, client):
        """Test creating a group with a duplicate active name fails with 400."""
        client.force_login(self.user)
        # Create one first
        ProjectGroupFactory(user=self.user, name="My Favorites")
        
        url = reverse("project:portfolio-group-create")
        post_data = {
            "name": "My Favorites",
            "project_ids": f"{self.project1.pk}"
        }
        response = client.post(url, data=json.dumps(post_data), content_type="application/json")
        assert response.status_code == 400
        data = response.json()
        assert "A group with this name already exists." in data["error"]

    def test_group_delete(self, client):
        """Test soft deleting a project group."""
        client.force_login(self.user)
        group = ProjectGroupFactory(user=self.user, name="Temporary Group")
        assert not group.deleted
        
        url = reverse("project:portfolio-group-delete", args=[group.pk])
        response = client.post(url)
        assert response.status_code == 302
        
        deleted_group = ProjectGroup.all_objects.get(pk=group.pk)
        assert deleted_group.deleted

    def test_group_cover_page_view(self, client, monkeypatch):
        """Test rendering the group cover page."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        group = ProjectGroupFactory(user=self.user, name="Favorites", projects=[self.project1, self.project2])
        
        url = reverse("project:portfolio-group-cover-page", args=[group.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert "portfolio/reports/group_cover_page.html" in [t.name for t in response.templates]

    def test_group_valuation_summary_view(self, client, monkeypatch):
        """Test rendering the grouped-by-province valuation summary."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        group = ProjectGroupFactory(user=self.user, name="Favorites", projects=[self.project1, self.project2])
        
        url = reverse("project:portfolio-group-valuation-summary", args=[group.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert "portfolio/reports/group_valuation_summary.html" in [t.name for t in response.templates]
        
        reports = response.context["province_reports"]
        # Gauteng and KwaZulu-Natal should be present
        assert len(reports) == 2
        assert reports[0]["province_name"] == "Gauteng"
        assert reports[1]["province_name"] == "KwaZulu-Natal"
        
        # Verify sub-totals
        assert reports[0]["budget"] == Decimal("100000.00")
        assert reports[1]["budget"] == Decimal("100000.00")
        assert response.context["total_budget"] == Decimal("200000.00")

    def test_group_cover_xlsx(self, client, monkeypatch):
        """Test downloading the group cover page XLSX."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        group = ProjectGroupFactory(user=self.user, name="Favorites", projects=[self.project1])
        
        url = reverse("project:portfolio-group-cover-page-xlsx", args=[group.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "cover_page.xlsx" in response["Content-Disposition"]

    def test_group_valuation_xlsx(self, client, monkeypatch):
        """Test downloading the group valuation summary XLSX."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        group = ProjectGroupFactory(user=self.user, name="Favorites", projects=[self.project1, self.project2])
        
        url = reverse("project:portfolio-group-valuation-summary-xlsx", args=[group.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "valuation_summary.xlsx" in response["Content-Disposition"]

    def test_multi_project_valuation_summary_view(self, client, monkeypatch):
        """Test rendering the ad-hoc multi project valuation summary grouped by province."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        
        url = reverse("project:portfolio-multi-valuation-summary") + f"?project_ids={self.project1.pk},{self.project2.pk}"
        response = client.get(url)
        assert response.status_code == 200
        assert "portfolio/reports/multi_project_valuation_summary.html" in [t.name for t in response.templates]
        
        reports = response.context["province_reports"]
        assert len(reports) == 2
        assert reports[0]["province_name"] == "Gauteng"
        assert reports[1]["province_name"] == "KwaZulu-Natal"
        assert response.context["total_budget"] == Decimal("200000.00")

    def test_multi_project_valuation_xlsx(self, client, monkeypatch):
        """Test downloading the ad-hoc multi project valuation summary XLSX grouped by province."""
        self._apply_mocks(monkeypatch)
        client.force_login(self.user)
        
        url = reverse("project:portfolio-multi-valuation-summary-xlsx") + f"?project_ids={self.project1.pk},{self.project2.pk}"
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "valuation_summary.xlsx" in response["Content-Disposition"]

