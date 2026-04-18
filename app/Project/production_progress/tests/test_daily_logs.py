"""Tests for Production Daily Log system."""

import json

import pytest
from django.urls import reverse

from app.Project.production_progress.factories import (
    DailyActivityEntryFactory,
    DailyActivityReportFactory,
    ProductionPlanFactory,
)
from app.Project.production_progress.production_models import (
    DailyActivityEntry,
    DailyActivityReport,
)


@pytest.mark.django_db
class TestProductionDailyLog:
    """Test cases for Production Daily Log views and logic."""

    def test_daily_log_list_view(self, client, project):
        """Test the list view displays daily reports."""
        user = project.users.first()
        client.force_login(user)

        report = DailyActivityReportFactory(project=project)
        DailyActivityEntryFactory(report=report)

        url = reverse(
            "project:production-daily-log-list", kwargs={"project_pk": project.pk}
        )
        response = client.get(url)

        assert response.status_code == 200
        assert report.date.strftime("%d %b %Y") in response.content.decode()

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
        report = DailyActivityReport.objects.get(project=project, date="2024-04-18")
        assert report.notes == "Testing submission"

        entry = DailyActivityEntry.objects.get(report=report)
        assert entry.production_plan == plan
        assert entry.hours_on_activity == 8.0
        assert entry.labour_usage.count() == 2
        assert entry.plant_usage.count() == 1

    def test_daily_log_detail_view(self, client, project):
        """Test the detail view shows report data."""
        user = project.users.first()
        client.force_login(user)

        report = DailyActivityReportFactory(project=project)
        entry = DailyActivityEntryFactory(report=report)

        url = reverse(
            "project:production-daily-log-detail",
            kwargs={"project_pk": project.pk, "pk": report.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert entry.production_plan.activity in response.content.decode()
