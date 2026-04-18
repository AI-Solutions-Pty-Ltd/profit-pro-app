import pytest

from app.Estimator.models import BOQItem
from app.Project.models.unit_models import UnitOfMeasure
from app.Project.production_progress.production_forms import ProductionPlanForm
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestProductionPlanForm:
    """Test cases for ProductionPlanForm."""

    def test_form_validation_with_wbs(self):
        """Test form validation with mandatory WBS fields."""
        project = ProjectFactory.create()
        # Create UnitOfMeasure for 'unit' field validation
        UnitOfMeasure.objects.create(name="Meter", short_name="m")
        # Create BOQItem to populate 'section' and 'bill_no' choices
        BOQItem.objects.create(
            project=project,
            section="Section A",
            bill_no="Bill 1",
            description="Test Item",
        )

        data = {
            "activity": "Test Activity",
            "section": "Section A",
            "bill_no": "Bill 1",
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
        assert "section" in form.errors
        assert "bill_no" in form.errors
