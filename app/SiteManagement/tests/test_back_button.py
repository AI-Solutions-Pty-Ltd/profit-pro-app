"""Tests for back button rendering in Site Management views."""

import pytest
from django.urls import reverse

from app.Project.tests.factories import ProjectFactory

pytestmark = pytest.mark.django_db


class TestBackButtonRendering:
    """Test cases for checking back button link target."""

    def test_back_button_points_to_company_management(self, client, superuser):
        """Test that the back button rendered in a list view links to company management."""
        client.force_login(superuser)
        project = ProjectFactory.create()
        project.users.add(superuser)

        # Let's hit the plant type list view which includes the back button
        url = reverse(
            "site_management:plant-type-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)

        assert response.status_code == 200

        # Verify the back button HTML anchor is present and targets company management
        expected_url = reverse(
            "project:company-management",
            kwargs={"pk": project.pk},
        )

        html_content = response.content.decode("utf-8")
        assert expected_url in html_content
        assert "Back" in html_content
