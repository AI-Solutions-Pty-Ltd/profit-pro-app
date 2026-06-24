"""Tests for project category hierarchy view and context."""

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
class TestCategoryHierarchyView:
    """Test cases for project category hierarchy in category_manage.html."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)

        # Assign user ADMIN role for project permissions
        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )

        # Construct the URL for CategoryListView
        self.url = reverse(
            "project:project-category-list",
            kwargs={"project_pk": self.project.pk},
        )

    def test_category_list_view_success(self, client):
        """Test that CategoryListView renders successfully and contains forms in context."""
        client.force_login(self.user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert "project/categories/category_manage.html" in [
            t.name for t in response.templates
        ]

        # Check context fields
        assert "category_form" in response.context
        assert "subcategory_form" in response.context
        assert "group_form" in response.context
        assert response.context["project"] == self.project

    def test_category_hierarchy_rendering(self, client):
        """Test that the nested Category, SubCategory, and Group structure renders correctly."""
        client.force_login(self.user)

        # Create Category, SubCategory, and Group
        category = CategoryFactory(project=self.project, name="L1 Category Test")
        subcategory = SubCategoryFactory(
            category=category, project=self.project, name="L2 SubCategory Test"
        )
        group = GroupFactory(
            sub_category=subcategory, project=self.project, name="L3 Group Test"
        )

        response = client.get(self.url)
        assert response.status_code == 200

        # Decode response content to check for nested items
        content = response.content.decode("utf-8")

        # Verify L1 Category is rendered
        assert "L1 Category Test" in content
        assert f"category-row-{category.pk}" in content

        # Verify L2 SubCategory is rendered
        assert "L2 SubCategory Test" in content
        assert f"subcategory-row-{subcategory.pk}" in content

        # Verify L3 Group is rendered
        assert "L3 Group Test" in content
        assert f"group-row-{group.pk}" in content

        # Verify collapsible containers exist
        assert f'id="category-{category.pk}"' in content
        assert f'id="subcategory-{subcategory.pk}"' in content
