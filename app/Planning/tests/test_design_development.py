import pytest
from django.urls import reverse

from app.Project.models import ProjectRole, Role
from app.Project.tests.factories import (
    AccountFactory,
    CategoryFactory,
    GroupFactory,
    ProjectFactory,
    SubCategoryFactory,
)


@pytest.mark.django_db
class TestDesignDevelopmentOverview:
    """Test cases for Design Development overview page."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)
        # Assign user ADMIN role for project permissions
        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )
        self.url = reverse(
            "planning:design-development-overview",
            kwargs={"project_pk": self.project.pk},
        )

    def test_overview_page_renders_correctly(self, client):
        """Test that the overview page renders category and subcategory structures."""
        client.force_login(self.user)
        category = CategoryFactory(project=self.project, name="Structural Category")
        subcategory = SubCategoryFactory(
            category=category, project=self.project, name="Concrete Subcategory"
        )
        GroupFactory(
            sub_category=subcategory, project=self.project, name="Foundations Group"
        )

        response = client.get(self.url)
        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Verify L1, L2, L3 titles are displayed
        assert "Structural Category" in content
        assert "Concrete Subcategory" in content
        assert "Foundations Group" in content

        # Verify the "No subcategories found for this category" is not shown when categories exist
        assert "No subcategories found for this category" not in content

    def test_empty_subcategory_renders_correct_message(self, client):
        """Test that a category with no subcategories displays the correct message."""
        client.force_login(self.user)
        CategoryFactory(project=self.project, name="Empty Category")

        response = client.get(self.url)
        assert response.status_code == 200
        content = response.content.decode("utf-8")

        assert "Empty Category" in content
        assert "No subcategories found for this category" in content
        assert "No categories found for this project" not in content
