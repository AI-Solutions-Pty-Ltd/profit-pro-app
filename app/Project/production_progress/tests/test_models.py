"""Tests for ProductionPlan models."""

import pytest

from decimal import Decimal
from datetime import date, timedelta
from app.Project.production_progress.factories import ProductionPlanFactory
from app.Estimator.factories import (
    ProjectPlantSpecificationFactory,
    ProjectPlantSpecificationComponentFactory,
    ProjectPlantCostFactory,
    BOQItemFactory
)


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

    def test_get_plant_allocations_direct(self):
        """Test get_plant_allocations with a direct specification assigned."""
        start = date(2024, 1, 1)
        finish = start + timedelta(days=5)

        plan = ProductionPlanFactory.create(
            start_date=start,
            finish_date=finish
        )
        # Verify duration was calculated correctly by model save()
        assert plan.duration == 5

        spec = ProjectPlantSpecificationFactory.create(project=plan.project)

        # Create components
        type1 = ProjectPlantCostFactory.create(project=plan.project, name="Excavator", hourly_rate=200)
        type2 = ProjectPlantCostFactory.create(project=plan.project, name="Dumper", hourly_rate=100)

        ProjectPlantSpecificationComponentFactory.create(specification=spec, plant_type=type1, hours=4)
        ProjectPlantSpecificationComponentFactory.create(specification=spec, plant_type=type2, hours=8)

        plan.plant_specification = spec
        plan.save()

        allocations = plan.get_plant_allocations()

        assert len(allocations) == 2

        # Excavator: 4 hrs/day * 5 days = 20 hrs. Cost = 20 * 200 = 4000
        excavator = next(a for a in allocations if a["name"] == "Excavator")
        assert excavator["hours_per_day"] == 4
        assert excavator["total_hours"] == 20
        assert excavator["total_cost"] == Decimal("4000.00")
        assert excavator["is_fallback"] is False

        # Dumper: 8 hrs/day * 5 days = 40 hrs. Cost = 40 * 100 = 4000
        dumper = next(a for a in allocations if a["name"] == "Dumper")
        assert dumper["hours_per_day"] == 8
        assert dumper["total_hours"] == 40
        assert dumper["total_cost"] == Decimal("4000.00")

        # Total plant cost should be 8000
        assert plan.total_plant_cost == Decimal("8000.00")

    def test_get_plant_allocations_fallback(self):
        """Test get_plant_allocations using fallback from BOQ items."""
        start = date(2024, 1, 1)
        finish = start + timedelta(days=2)

        plan = ProductionPlanFactory.create(
            start_date=start,
            finish_date=finish,
            section="S1",
            bill_no="B1"
        )
        assert plan.duration == 2

        spec = ProjectPlantSpecificationFactory.create(project=plan.project, name="Fallback Spec")

        type1 = ProjectPlantCostFactory.create(project=plan.project, name="Roller", hourly_rate=300)
        ProjectPlantSpecificationComponentFactory.create(specification=spec, plant_type=type1, hours=6)

        # Link spec to BOQItem
        BOQItemFactory.create(
            project=plan.project,
            section="S1",
            bill_no="B1",
            plant_specification=spec
        )

        # Plan has NO direct spec
        plan.plant_specification = None
        plan.save()

        allocations = plan.get_plant_allocations()

        assert len(allocations) == 1
        roller = allocations[0]
        assert roller["name"] == "Roller"
        assert roller["total_hours"] == 12 # 6 hrs/day * 2 days
        assert roller["total_cost"] == Decimal("3600.00")
        assert roller["is_fallback"] is True

        assert plan.total_plant_cost == Decimal("3600.00")
