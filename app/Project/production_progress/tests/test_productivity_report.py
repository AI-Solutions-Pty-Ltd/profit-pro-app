"""Tests for the Productivity Report utilities and dashboards."""

from decimal import Decimal

import pytest

from app.Project.production_progress.utils.production_utils import (
    get_project_productivity_report_data,
)


@pytest.mark.django_db
class TestProductivityReportEmpty:
    """Test cases for productivity report data when there are no projects."""

    def test_empty_project_list_graceful_handling(self):
        """Test that passing an empty project list does not crash and returns safe defaults."""
        data = get_project_productivity_report_data([])
        assert data is not None
        assert "summary" in data
        assert "charts" in data
        assert "forecasts" in data
        assert "activities" in data

        summary = data["summary"]
        assert summary["total_planned_qty"] == Decimal("0")
        assert summary["total_produced_qty"] == Decimal("0")
        assert summary["total_actual_cost"] == Decimal("0")
        assert summary["total_planned_cost"] == Decimal("0")
        assert summary["ppi"] == 1.0
        assert summary["cpi"] == 1.0
        assert summary["overall_progress_pct"] == 0

    def test_none_project_list_graceful_handling(self):
        """Test that passing None as project_ids does not crash and returns safe defaults."""
        data = get_project_productivity_report_data(None)
        assert data is not None
        assert "summary" in data

        summary = data["summary"]
        assert summary["total_planned_qty"] == Decimal("0")
        assert summary["ppi"] == 1.0
