"""Tests for Overhead Daily Log model and views."""

import pytest
from django.urls import reverse

from app.Project.tests.factories import OverheadEntityFactory, ProjectFactory
from app.SiteManagement.models import OverheadDailyLog
from app.SiteManagement.tests.factories import OverheadDailyLogFactory

pytestmark = pytest.mark.django_db


class TestOverheadDailyLogModel:
    """Test cases for OverheadDailyLog model."""

    def test_overhead_daily_log_creation(self):
        """Test creating an overhead daily log with valid data."""
        project = ProjectFactory()
        entity = OverheadEntityFactory(
            project=project, name="Test Overhead", category="Utilities"
        )
        log = OverheadDailyLogFactory(project=project, overhead_entity=entity)

        assert log.id is not None  # type: ignore
        assert log.project == project
        assert log.overhead_entity == entity
        assert log.description == "Test Overhead"  # type: ignore
        assert log.category == "Utilities"  # type: ignore

    def test_overhead_daily_log_sync_on_save(self):
        """Test that fields are synchronized from entity on save."""
        project = ProjectFactory()
        entity = OverheadEntityFactory(
            project=project, name="Sync Test", category="Sync Cat"
        )
        log = OverheadDailyLog(
            project=project,
            overhead_entity=entity,
            date="2023-01-01",
            quantity=10,
        )
        log.save()

        assert log.description == "Sync Test"
        assert log.category == "Sync Cat"

    def test_str_method(self):
        """Test the __str__ method."""
        log = OverheadDailyLogFactory(description="String Test", date="2023-10-10")
        assert str(log) == "String Test - 2023-10-10"


class TestOverheadDailyLogViews:
    """Test cases for OverheadDailyLog views."""

    def test_overhead_daily_log_list_view(self, client, superuser):
        """Test the list view."""
        client.force_login(superuser)
        project = ProjectFactory()
        # Add user to project to pass permission checks
        project.users.add(superuser)

        OverheadDailyLogFactory(project=project)

        url = reverse(
            "site_management:overhead-log-list",
            kwargs={"project_pk": project.pk},  # type: ignore
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "overhead_logs" in response.context
        assert len(response.context["overhead_logs"]) == 1

    def test_overhead_daily_log_create_view(self, client, superuser):
        """Test the create view."""
        client.force_login(superuser)
        project = ProjectFactory()
        project.users.add(superuser)
        entity = OverheadEntityFactory(project=project)

        url = reverse(
            "site_management:overhead-log-create",
            kwargs={"project_pk": project.pk},  # type: ignore
        )
        data = {
            "overhead_entity": entity.pk,  # type: ignore
            "date": "2023-01-01",
            "quantity": "150.00",
            "remarks": "Test Remarks",
        }
        response = client.post(url, data)

        assert response.status_code == 302
        assert OverheadDailyLog.objects.filter(remarks="Test Remarks").exists()

    def test_overhead_daily_log_update_view(self, client, superuser):
        """Test the update view."""
        client.force_login(superuser)
        project = ProjectFactory()
        project.users.add(superuser)
        # Ensure entity is linked to the same project
        log = OverheadDailyLogFactory(
            project=project, overhead_entity__project=project, remarks="Old Remarks"
        )

        url = reverse(
            "site_management:overhead-log-update",
            kwargs={"project_pk": project.pk, "pk": log.pk},  # type: ignore
        )
        data = {
            "overhead_entity": log.overhead_entity.pk,  # type: ignore
            "date": "2023-01-01",
            "quantity": "200.00",
            "remarks": "New Remarks",
        }
        response = client.post(url, data)

        assert response.status_code == 302
        log.refresh_from_db()  # type: ignore
        assert log.remarks == "New Remarks"
        assert log.quantity == 200

    def test_overhead_daily_log_delete_view(self, client, superuser):
        """Test the delete view."""
        client.force_login(superuser)
        project = ProjectFactory()
        project.users.add(superuser)
        log = OverheadDailyLogFactory(project=project)

        url = reverse(
            "site_management:overhead-log-delete",
            kwargs={"project_pk": project.pk, "pk": log.pk},  # type: ignore
        )
        response = client.post(url)

        assert response.status_code == 302
        # Check for soft delete - refresh_from_db fails if objects manager filters it out
        # We use all_objects to check the state
        deleted_log = OverheadDailyLog.all_objects.get(pk=log.pk)  # type: ignore
        assert deleted_log.deleted is True
