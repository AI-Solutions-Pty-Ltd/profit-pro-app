from datetime import timedelta

import pytest
from django.utils import timezone

from app.Estimator.models import ProjectLabourSpecification, ProjectPlantSpecification
from app.Project.production_progress.production_models import ProductionPlan
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestProductionHierarchy:
    """Tests for ProductionPlan hierarchy and date synchronization."""

    def test_hierarchy_creation_on_save(self):
        """Test that parents are automatically created for a leaf activity."""
        project = ProjectFactory()
        labour = ProjectLabourSpecification.objects.create(
            project=project, name="Labour Spec"
        )

        plan = ProductionPlan.objects.create(
            project=project,
            labour_activity=labour,
            section="Section A",
            bill_no="1.1",
            activity="Test Activity",
            start_date=timezone.now().date(),
            finish_date=timezone.now().date() + timedelta(days=5),
            quantity=100,
            unit="m2",
        )

        # Verify hierarchy
        assert plan.parent is not None
        assert plan.parent.node_type == "BILL"
        assert plan.parent.activity == "Bill 1.1"
        assert plan.parent.parent is not None
        assert plan.parent.parent.node_type == "SECTION"
        assert plan.parent.parent.activity == "Section A"

    def test_date_sync_upwards(self):
        """Test that updating a child's dates updates the parent and grandparent."""
        project = ProjectFactory()
        labour = ProjectLabourSpecification.objects.create(
            project=project, name="Labour Spec"
        )

        today = timezone.now().date()
        plan = ProductionPlan.objects.create(
            project=project,
            labour_activity=labour,
            section="Sync Section",
            activity="Act 1",
            start_date=today,
            finish_date=today + timedelta(days=2),
            quantity=1,
            unit="m2",
        )

        section = plan.parent
        assert section.start_date == today
        assert section.finish_date == today + timedelta(days=2)

        # Add another child with a wider range
        plan2 = ProductionPlan.objects.create(
            project=project,
            labour_activity=labour,
            section="Sync Section",
            activity="Act 2",
            start_date=today - timedelta(days=5),
            finish_date=today + timedelta(days=10),
            quantity=1,
            unit="m2",
        )

        # Section should now span the widest range
        section.refresh_from_db()
        assert section.start_date == today - timedelta(days=5)
        assert section.finish_date == today + timedelta(days=10)

    def test_auto_cleanup_on_delete(self):
        """Test that parents are deleted when their last child is deleted."""
        project = ProjectFactory()
        labour = ProjectLabourSpecification.objects.create(
            project=project, name="Labour Spec"
        )

        plan = ProductionPlan.objects.create(
            project=project,
            labour_activity=labour,
            section="Cleanup Section",
            activity="Only Child",
            quantity=1,
            unit="m2",
        )

        section_id = plan.parent.id
        assert ProductionPlan.objects.filter(id=section_id).exists()

        # Delete the only child
        plan.soft_delete()

        # Section should be gone (soft-deleted)
        assert not ProductionPlan.objects.filter(id=section_id, deleted=False).exists()

    def test_plant_only_activity_hierarchy(self):
        """Test that plant-only activities also trigger hierarchy generation."""
        project = ProjectFactory()
        plant = ProjectPlantSpecification.objects.create(
            project=project, name="Plant Spec"
        )

        plan = ProductionPlan.objects.create(
            project=project,
            plant_specification=plant,
            section="Plant Section",
            activity="Excavator Work",
            quantity=1,
            unit="m2",
        )

        assert plan.parent is not None
        assert plan.parent.node_type == "SECTION"
        assert plan.parent.activity == "Plant Section"
