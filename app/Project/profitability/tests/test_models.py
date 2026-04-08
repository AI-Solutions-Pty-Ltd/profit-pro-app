import pytest

from app.Project.profitability.tests.factories import (
    JournalEntryFactory,
    LabourCostTrackerFactory,
    OverheadCostTrackerFactory,
    SubcontractorCostTrackerFactory,
)


@pytest.mark.django_db
class TestProfitabilityModels:
    """Test cases for Profitability submodule models."""

    def test_journal_entry_creation(self):
        """Test creating a journal entry."""
        entry = JournalEntryFactory(description="Test Entry", amount=150.50)
        assert entry.id is not None  # type: ignore
        assert str(entry) == f"{entry.date} - Test Entry"
        assert entry.amount == 150.50

    def test_subcontractor_tracker_creation(self):
        """Test creating a subcontractor cost tracker."""
        tracker = SubcontractorCostTrackerFactory(amount_of_days=5.0, rate=100.0)
        assert tracker.id is not None  # type: ignore
        assert tracker.total_cost == 500.0  # type: ignore

    def test_labour_tracker_creation(self):
        """Test creating a labour cost tracker."""
        tracker = LabourCostTrackerFactory(amount_of_days=2.5, salary=200.0)
        assert tracker.id is not None  # type: ignore
        assert tracker.total_cost == 500.0  # type: ignore

    def test_overhead_tracker_creation(self):
        """Test creating an overhead cost tracker."""
        tracker = OverheadCostTrackerFactory(name="Electric Bill", amount=1200.0)
        assert tracker.id is not None  # type: ignore
        assert str(tracker) == "Electric Bill"
