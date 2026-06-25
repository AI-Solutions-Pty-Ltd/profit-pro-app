import json

import pytest
from django.urls import reverse

from app.Project.tests.factories import AccountFactory, ProjectFactory


@pytest.mark.django_db
class TestProjectReportConfig:
    """Test cases for ProjectReportConfigView."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)
        # Assign user a project role to pass permission checking if needed
        from app.Project.models import ProjectRole, Role

        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )
        self.url = reverse(
            "project:project-report-config", kwargs={"pk": self.project.pk}
        )

    def test_get_report_config(self, client):
        """Test successfully rendering report config page."""
        client.force_login(self.user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert "project/report_config.html" in [t.name for t in response.templates]

    def test_save_report_config_success(self, client):
        """Test successfully saving column configuration and verifying resolution order."""
        client.force_login(self.user)

        column_data = {
            "columns": [
                {"id": "description", "label": "DESC", "enabled": True},
                {"id": "item_number", "label": "ITEM CODE", "enabled": True},
            ]
        }

        data = {
            "action": "save_report_config",
            "column_config": json.dumps(column_data),
        }

        response = client.post(self.url, data)
        assert response.status_code == 302

        self.project.refresh_from_db()
        assert self.project.column_config == column_data

        # Verify get_column_config() resolves the first two columns in the saved custom order
        resolved_cols = self.project.get_column_config()
        assert resolved_cols[0]["id"] == "description"
        assert resolved_cols[0]["label"] == "DESC"
        assert resolved_cols[1]["id"] == "item_number"
        assert resolved_cols[1]["label"] == "ITEM CODE"


@pytest.mark.django_db
class TestProjectCoverConfig:
    """Test cases for ProjectCoverConfigView."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)
        from app.Project.models import ProjectRole, Role

        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )
        self.url = reverse(
            "project:project-cover-config", kwargs={"pk": self.project.pk}
        )

    def test_get_cover_config(self, client):
        """Test successfully rendering cover config page."""
        client.force_login(self.user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert "project/cover_config.html" in [t.name for t in response.templates]

    def test_save_cover_config_success(self, client):
        """Test successfully saving cover page configuration."""
        client.force_login(self.user)

        cover_data = {
            "title": "CUSTOM COVER TITLE",
            "sections": {
                "section_a": {
                    "title": "CUSTOM SECTION A",
                    "fields": [
                        {
                            "id": "contract_name",
                            "label": "Custom Contract Label",
                            "enabled": True,
                        }
                    ],
                }
            },
        }

        data = {
            "action": "save_cover_config",
            "cover_config": json.dumps(cover_data),
        }

        response = client.post(self.url, data)
        assert response.status_code == 302

        self.project.refresh_from_db()
        assert self.project.cover_page_config == cover_data

        # Verify get_cover_page_config() resolves the custom title and field correctly
        resolved_config = self.project.get_cover_page_config()
        assert resolved_config["title"] == "CUSTOM COVER TITLE"
        sec_a_fields = resolved_config["sections"]["section_a"]["fields"]
        contract_field = next(f for f in sec_a_fields if f["id"] == "contract_name")
        assert contract_field["label"] == "Custom Contract Label"
        assert contract_field["enabled"] is True

    def test_default_cover_config_has_custom_ledger_fields(self):
        """Test default cover page config contains custom ledger fields."""
        resolved = self.project.get_cover_page_config()
        fields = resolved["sections"]["section_c"]["fields"]
        field_ids = [f["id"] for f in fields]
        assert "advance_payment" in field_ids
        assert "retention" in field_ids
        assert "material_on_site" in field_ids
        assert "other_specify" in field_ids


@pytest.mark.django_db
class TestCompanyManagementSiteCards:
    """Test cases for CompanyManagementView site management cards."""

    def test_company_management_site_cards_rendering(self, client):
        """Test that company management view renders biweekly safety and ncr cards."""
        user = AccountFactory()
        project = ProjectFactory()
        project.users.add(user)

        client.force_login(user)
        url = reverse("project:company-management", kwargs={"pk": project.pk})
        response = client.get(url)

        assert response.status_code == 200

        # Check for Bi-Weekly Safety Card
        expected_safety_url = reverse(
            "site_management:biweekly-safety-list",
            kwargs={"project_pk": project.pk},
        )
        assert expected_safety_url in response.content.decode("utf-8")
        assert "Bi-Weekly Safety" in response.content.decode("utf-8")

        # Check for NCR Register Card
        expected_ncr_url = reverse(
            "site_management:ncr-list",
            kwargs={"project_pk": project.pk},
        )
        assert expected_ncr_url in response.content.decode("utf-8")
        assert "NCR Register" in response.content.decode("utf-8")


@pytest.mark.django_db
class TestProjectSetup:
    """Test cases for ProjectSetupView."""

    def test_setup_milestones_card_renders(self, client):
        """Test that project setup view renders Setup Construction Milestones card."""
        user = AccountFactory()
        project = ProjectFactory()
        project.users.add(user)
        # Assign user a project role to pass permission checking
        from app.Project.models import ProjectRole, Role

        ProjectRole.objects.get_or_create(project=project, user=user, role=Role.ADMIN)

        client.force_login(user)
        url = reverse("project:project-setup", kwargs={"pk": project.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Setup Construction Milestones" in content
        expected_milestones_url = reverse(
            "project:project-milestone-setup",
            kwargs={"project_pk": project.pk},
        )
        assert expected_milestones_url in content


@pytest.mark.django_db
class TestProjectListViewFilters:
    """Test cases for ProjectListView filtering and searching."""

    def test_filter_by_search_name(self, client):
        from django.urls import reverse

        from app.Account.tests.factories import SuperuserFactory
        from app.Project.tests.factories import ProjectFactory

        admin = SuperuserFactory()
        client.force_login(admin)

        p1 = ProjectFactory(name="Alpha Project")
        p2 = ProjectFactory(name="Beta Project")

        url = reverse("project:project-list")
        
        # Search for "Alpha"
        response = client.get(url, data={"search": "Alpha"})
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Alpha Project" in content
        assert "Beta Project" not in content

    def test_filter_by_province(self, client):
        from django.urls import reverse

        from app.Account.tests.factories import (
            MunicipalityFactory,
            ProvinceFactory,
            SuperuserFactory,
        )
        from app.Project.tests.factories import ProjectFactory

        admin = SuperuserFactory()
        client.force_login(admin)

        prov1 = ProvinceFactory(name="Gauteng")
        prov2 = ProvinceFactory(name="Western Cape")

        mun1 = MunicipalityFactory(province=prov1)
        mun2 = MunicipalityFactory(province=prov2)

        p1 = ProjectFactory(name="Joburg Project", area=mun1)
        p2 = ProjectFactory(name="Cape Town Project", area=mun2)

        url = reverse("project:project-list")

        # Filter by Gauteng
        response = client.get(url, data={"province": prov1.pk})
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Joburg Project" in content
        assert "Cape Town Project" not in content

    def test_filter_by_municipality(self, client):
        from django.urls import reverse

        from app.Account.tests.factories import (
            MunicipalityFactory,
            ProvinceFactory,
            SuperuserFactory,
        )
        from app.Project.tests.factories import ProjectFactory

        admin = SuperuserFactory()
        client.force_login(admin)

        prov = ProvinceFactory()
        mun1 = MunicipalityFactory(province=prov, municipality_name="Mun One")
        mun2 = MunicipalityFactory(province=prov, municipality_name="Mun Two")

        p1 = ProjectFactory(name="Project One", area=mun1)
        p2 = ProjectFactory(name="Project Two", area=mun2)

        url = reverse("project:project-list")

        # Filter by Mun One
        response = client.get(url, data={"area": mun1.pk})
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Project One" in content
        assert "Project Two" not in content

