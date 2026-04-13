"""Tests for ProductionPlan forms."""

import pytest
from app.Project.production_progress.production_forms import ProductionPlanForm
from app.Project.tests.factories import ProjectFactory
from app.BillOfQuantities.tests.factories import StructureFactory, BillFactory, PackageFactory

@pytest.mark.django_db
class TestProductionPlanForm:
    """Test cases for ProductionPlanForm."""

    def test_form_validation_with_wbs(self):
        """Test form validation with mandatory WBS fields."""
        project = ProjectFactory.create()
        structure = StructureFactory.create(project=project)
        bill = BillFactory.create(structure=structure)
        package = PackageFactory.create(bill=bill)

        data = {
            "activity": "Test Activity",
            "structure": structure.id,
            "bill": bill.id,
            "package": package.id,
            "start_date": "2026-04-12",
            "finish_date": "2026-04-22",
            "quantity": 100,
            "unit": "m",
        }
        form = ProductionPlanForm(data=data, project_id=project.id)
        assert form.is_valid(), form.errors

    def test_form_validation_missing_wbs(self):
        """Test form validation fails when WBS fields are missing."""
        project = ProjectFactory.create()
        data = {
            "activity": "Test Activity",
            "start_date": "2026-04-12",
            "finish_date": "2026-04-22",
            "quantity": 100,
            "unit": "m",
        }
        form = ProductionPlanForm(data=data, project_id=project.id)
        assert not form.is_valid()
        assert "structure" in form.errors
        assert "bill" in form.errors
        assert "package" in form.errors
