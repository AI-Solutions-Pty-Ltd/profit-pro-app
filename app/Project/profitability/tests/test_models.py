import pytest

from app.Project.profitability.tests.factories import (
    JournalEntryFactory,
    LabourCostTrackerFactory,
    OverheadCostTrackerFactory,
    SubcontractorCostTrackerFactory,
)
from app.Project.tests.factories import OverheadEntityFactory, ProjectFactory


@pytest.mark.django_db
class TestProfitabilityModels:
    """Test cases for Profitability submodule models."""

    def test_journal_entry_creation(self):
        """Test creating a journal entry."""
        from decimal import Decimal

        entry = JournalEntryFactory(
            description="Test Entry", amount=Decimal("150.50"), category="REVENUE"
        )
        assert entry.id is not None  # type: ignore
        assert str(entry) == f"{entry.date} - REVENUE - 150.50"
        assert entry.amount == Decimal("150.50")

    def test_subcontractor_tracker_creation(self):
        """Test creating a subcontractor cost tracker."""
        from decimal import Decimal

        tracker = SubcontractorCostTrackerFactory(
            amount_of_days=Decimal("5.0"), rate=Decimal("100.0")
        )
        assert tracker.id is not None  # type: ignore
        assert tracker.cost == Decimal("500.0")  # type: ignore

    def test_labour_tracker_creation(self):
        """Test creating a labour cost tracker."""
        from decimal import Decimal

        tracker = LabourCostTrackerFactory(
            amount_of_days=Decimal("2.5"), salary=Decimal("200.0")
        )
        assert tracker.id is not None  # type: ignore
        assert tracker.cost == Decimal("500.0")  # type: ignore

    def test_overhead_tracker_creation(self):
        """Test creating an overhead cost tracker."""
        from decimal import Decimal

        project = ProjectFactory()
        entity = OverheadEntityFactory(project=project, name="Electric Bill")
        tracker = OverheadCostTrackerFactory(
            project=project,
            overhead_entity=entity,
            amount_of_days=Decimal("1.0"),
            rate=Decimal("1200.0"),
        )
        assert tracker.id is not None  # type: ignore
        assert str(tracker) == f"Electric Bill - {tracker.date} - 1200.00"

    def test_subcontractor_tracker_null_entity(self):
        """Test creating a subcontractor cost tracker without an entity."""
        from decimal import Decimal

        from app.Project.models import SubcontractorCostTracker

        tracker = SubcontractorCostTracker.objects.create(
            project=ProjectFactory(),
            subcontractor_entity=None,
            date="2024-01-01",
            amount_of_days=Decimal("1.0"),
            rate=Decimal("50.0"),
        )
        assert tracker.id is not None
        assert tracker.subcontractor_entity is None
        assert tracker.cost == Decimal("50.0")
        assert str(tracker) == "Unknown - 2024-01-01 - 50.00"
