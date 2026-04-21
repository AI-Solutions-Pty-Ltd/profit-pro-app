"""Tests for ProductionPlan models."""

import pytest

from app.Project.production_progress.factories import ProductionPlanFactory


@pytest.mark.django_db
class TestProductionPlanModel:
    """Test cases for ProductionPlan model."""

    def test_production_plan_creation(self):
        """Test creating a production plan with mandatory WBS fields."""
        plan = ProductionPlanFactory.create(section="Section A", bill_no="Bill 1")
        assert plan.id is not None
        assert plan.section == "Section A"
        assert plan.bill_no == "Bill 1"

    def test_production_plan_str(self):
        """Test the string representation of ProductionPlan."""
        plan = ProductionPlanFactory.create(activity="Excavation")
        assert str(plan) == f"{plan.project.name} - Excavation"

    def test_production_plan_nullable_dates(self):
        """Test creating a production plan without start and finish dates."""
        plan = ProductionPlanFactory.create(
            start_date=None, finish_date=None, daily_rate=150.50
        )
        assert plan.id is not None
        assert plan.start_date is None
        assert plan.finish_date is None
        assert plan.daily_rate == 150.50
