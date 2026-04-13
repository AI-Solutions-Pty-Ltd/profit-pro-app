"""Tests for ProductionPlan models."""

import pytest
from app.Project.production_progress.factories import ProductionPlanFactory

@pytest.mark.django_db
class TestProductionPlanModel:
    """Test cases for ProductionPlan model."""

    def test_production_plan_creation(self):
        """Test creating a production plan with mandatory WBS fields."""
        plan = ProductionPlanFactory.create()
        assert plan.id is not None
        assert plan.structure is not None
        assert plan.bill is not None
        assert plan.package is not None
        assert plan.structure.project == plan.project
        assert plan.bill.structure == plan.structure
        assert plan.package.bill == plan.bill

    def test_production_plan_str(self):
        """Test the string representation of ProductionPlan."""
        plan = ProductionPlanFactory.create(activity="Excavation")
        assert str(plan) == f"{plan.project.name} - Excavation"
