"""Tests for the reusable project configuration navigation tabs."""

import pytest
from django.urls import reverse

from app.Project.models import ProjectRole, Role
from app.Project.tests.factories import AccountFactory, ProjectFactory


@pytest.mark.django_db
class TestNavigationTabsView:
    """Test cases verifying the navigation tabs render correctly across all pages."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)

        # Assign user ADMIN role for project permissions
        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )

    def test_navigation_tabs_on_all_pages(self, client):
        """Test that navigation tabs render on category, discipline, drawing type, and milestone pages."""
        client.force_login(self.user)

        pages = [
            ("project:project-category-list", "WBS Levels"),
            ("project:project-discipline-list", "Disciplines"),
            ("project:project-drawing-type-list", "Drawing Types"),
            ("project:project-milestone-setup", "Construction Milestones"),
        ]

        for url_name, _ in pages:
            url = reverse(url_name, kwargs={"project_pk": self.project.pk})
            response = client.get(url)
            assert response.status_code == 200

            content = response.content.decode("utf-8")
            # Verify the navigation tabs include is loaded by checking for tab names
            assert "WBS Levels" in content
            assert "Disciplines" in content
            assert "Drawing Types" in content
            assert "Construction Milestones" in content
