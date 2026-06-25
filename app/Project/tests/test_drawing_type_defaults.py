"""Tests for DrawingTypeLoadDefaultsView."""

import pytest
from django.urls import reverse

from app.Project.models import DrawingType, ProjectRole, Role
from app.Project.tests.factories import AccountFactory, DrawingTypeFactory, ProjectFactory


@pytest.mark.django_db
class TestDrawingTypeLoadDefaultsView:
    """Test cases for DrawingTypeLoadDefaultsView."""

    def setup_method(self):
        from django.db.models.signals import post_save
        import factory

        with factory.django.mute_signals(post_save):
            self.project = ProjectFactory()

        self.user = AccountFactory()
        self.project.users.add(self.user)

        # Assign user ADMIN role for project permissions
        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )

        self.url = reverse(
            "project:project-drawing-type-load-defaults",
            kwargs={"project_pk": self.project.pk},
        )

    def test_load_defaults_success(self, client):
        """Test loading defaults successfully when none exist."""
        client.force_login(self.user)

        # Ensure no drawing types exist initially
        assert DrawingType.objects.filter(project=self.project, deleted=False).count() == 0

        response = client.post(self.url)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert len(data["created"]) == 4
        assert len(data["skipped"]) == 0

        # Verify created names
        expected_names = {"Construction", "Information", "Shop", "Tender"}
        actual_names = set(
            DrawingType.objects.filter(project=self.project, deleted=False)
            .values_list("name", flat=True)
        )
        assert actual_names == expected_names

        # Verify descriptions are also populated
        construction_dt = DrawingType.objects.get(project=self.project, name="Construction")
        assert construction_dt.description == "Construction drawing type"

    def test_load_defaults_idempotent(self, client):
        """Test loading defaults when some already exist skips duplicates."""
        client.force_login(self.user)

        # Pre-create "Construction" and "Shop"
        DrawingTypeFactory(project=self.project, name="Construction", description="Existing construction")
        DrawingTypeFactory(project=self.project, name="Shop", description="Existing shop")

        assert DrawingType.objects.filter(project=self.project, deleted=False).count() == 2

        response = client.post(self.url)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert set(data["created"]) == {"Information", "Tender"}
        assert set(data["skipped"]) == {"Construction", "Shop"}

        # Total drawing types should be 4
        assert DrawingType.objects.filter(project=self.project, deleted=False).count() == 4

        # Descriptions of pre-existing ones should not change
        construction_dt = DrawingType.objects.get(project=self.project, name="Construction")
        assert construction_dt.description == "Existing construction"

        # Descriptions of new ones should be populated
        information_dt = DrawingType.objects.get(project=self.project, name="Information")
        assert information_dt.description == "Information drawing type"

    def test_load_defaults_case_insensitive(self, client):
        """Test case-insensitive duplicate checks."""
        client.force_login(self.user)

        # Pre-create "tender" in lowercase
        DrawingTypeFactory(project=self.project, name="tender", description="lowercase tender")

        response = client.post(self.url)
        assert response.status_code == 200

        data = response.json()
        assert "Tender" in data["skipped"]
        assert "Tender" not in data["created"]
