import json

import pytest
from django.urls import reverse

from app.Project.tests.factories import AccountFactory, ProjectFactory


@pytest.mark.django_db
class TestProjectSetupReportConfig:
    """Test cases for ProjectSetupView report configuration action."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)
        # Assign user a project role to pass permission checking if needed
        from app.Project.models import ProjectRole, Role

        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )
        self.url = reverse("project:project-setup", kwargs={"pk": self.project.pk})

    def test_save_report_config_success(self, client):
        """Test successfully saving certificate layout and column configuration."""
        client.force_login(self.user)

        column_data = {
            "columns": [
                {"id": "item_number", "label": "ITEM CODE", "enabled": True},
                {"id": "description", "label": "DESC", "enabled": True},
            ]
        }

        data = {
            "action": "save_report_config",
            "certificate_layout": "LEPHADIMISHA",
            "column_config": json.dumps(column_data),
        }

        response = client.post(self.url, data)
        assert response.status_code == 302

        self.project.refresh_from_db()
        assert self.project.certificate_layout == "LEPHADIMISHA"
        assert self.project.column_config == column_data


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
