"""Tests for Production Daily Log system."""

import json

import pytest
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Project.production_progress.factories import (
    DailyActivityEntryFactory,
    ProductionPlanFactory,
    ProductionResourceFactory,
)
from app.Project.production_progress.production_models import (
    DailyActivityEntry,
)


@pytest.mark.django_db
class TestProductionDailyLog:
    """Test cases for Production Daily Log views and logic."""

    def test_daily_log_list_view(self, client, project):
        """Test the list view displays daily log entries."""
        user = project.users.first()
        client.force_login(user)

        entry = DailyActivityEntryFactory(project=project)

        url = reverse(
            "project:production-daily-log-list", kwargs={"project_pk": project.pk}
        )
        response = client.get(url)

        assert response.status_code == 200
        assert entry.date.strftime("%d %b %Y") in response.content.decode()

    def test_daily_log_ajax_data_view(self, client, project):
        """Test the AJAX view returns activity metadata."""
        user = project.users.first()
        client.force_login(user)

        plan = ProductionPlanFactory(project=project, unit="m3")

        url = reverse(
            "project:ajax-daily-log-activity-data", kwargs={"project_pk": project.pk}
        )
        response = client.get(f"{url}?plan_id={plan.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["unit"] == "m3"

    def test_daily_log_create_submission(self, client, project):
        """Test submitting a new daily log via JSON POST."""
        user = project.users.first()
        client.force_login(user)

        plan = ProductionPlanFactory(project=project)

        url = reverse(
            "project:production-daily-log-create", kwargs={"project_pk": project.pk}
        )
        payload = {
            "date": "2024-04-18",
            "notes": "Testing submission",
            "entries": [
                {
                    "production_plan_id": str(plan.id),
                    "quantity": 50,
                    "hours_on_activity": 8,
                    "labour_details": {
                        "Skilled": {"number": 2, "hours": 8},
                        "General": {"number": 4, "hours": 8},
                    },
                    "plant_usage": [
                        {"plant_name": "Excavator 20T", "hours": 8, "quantity": 50}
                    ],
                }
            ],
        }

        response = client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify database
        entry = DailyActivityEntry.objects.get(project=project, date="2024-04-18")
        assert entry.notes == "Testing submission"
        assert entry.production_plan == plan
        assert float(entry.hours_on_activity) == 8.0

    def test_daily_log_detail_view(self, client, project):
        """Test the detail view shows entry data."""
        user = project.users.first()
        client.force_login(user)

        entry = DailyActivityEntryFactory(project=project)

        url = reverse(
            "project:production-daily-log-detail",
            kwargs={"project_pk": project.pk, "pk": entry.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert entry.production_plan.activity in response.content.decode()

    def test_granular_update_serializer(self, client):
        """Test that updating a single entry via serializer works."""
        entry = DailyActivityEntryFactory()
        user = AccountFactory()
        client.force_login(user)

        project = entry.project
        plan = entry.production_plan

        # Create a resource for the plan to match the payload
        ProductionResourceFactory(
            production_plan=plan, name="Excavator", resource_type="PLANT"
        )

        url = reverse(
            "project:production-daily-log-entry-edit",
            kwargs={"project_pk": project.pk, "pk": entry.pk},
        )

        # New data for the entry
        payload = {
            "production_plan_id": plan.id,
            "quantity": 50.0,
            "hours_on_activity": 10.0,
            "labour_details": {
                "Skilled": {"number": 2, "hours": 8},
                "Semi-Skilled": {"number": 1, "hours": 8},
            },
            "plant_usage": [{"plant_name": "Excavator", "hours": 5}],
        }

        response = client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify database
        entry.refresh_from_db()
        assert float(entry.quantity) == 50.0
        assert float(entry.hours_on_activity) == 10.0

        # Verify usage
        assert entry.labour_usage.count() == 2
        assert entry.plant_usage.count() == 1
        assert entry.plant_usage.first().resource.name == "Excavator"

    def test_granular_update_initial_data(self, client):
        """Test that the edit view returns the correct initial data."""
        entry = DailyActivityEntryFactory(quantity=25.0, hours_on_activity=8.0)
        user = AccountFactory()
        client.force_login(user)

        project = entry.project

        url = reverse(
            "project:production-daily-log-entry-edit",
            kwargs={"project_pk": project.pk, "pk": entry.pk},
        )

        response = client.get(url)
        assert response.status_code == 200

        # Check context
        initial_data = response.context["initial_data"]
        data = json.loads(initial_data)

        assert data["quantity"] == 25.0
        assert data["hours_on_activity"] == 8.0
        assert data["production_plan_id"] == entry.production_plan.id
