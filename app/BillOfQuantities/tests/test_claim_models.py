"""Tests for Claim models."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError

from app.BillOfQuantities.models import Claim
from app.BillOfQuantities.tests.factories import ClaimFactory, LineItemFactory
from app.Project.tests.factories import PlannedValueFactory, ProjectFactory


class TestClaimModel:
    """Test cases for Claim model."""

    def test_claim_creation(self):
        """Test creating a claim with valid data."""
        project = ProjectFactory.create(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )
        claim = ClaimFactory.create(
            project=project,
            period=date(2024, 6, 1),
            estimated_claim=150000.00,
            notes="Test claim",
        )
        assert claim.id is not None
        assert claim.project == project
        assert claim.period == date(2024, 6, 1)
        assert claim.estimated_claim == 150000.00
        assert claim.notes == "Test claim"

    def test_claim_str(self):
        """Test claim string representation."""
        claim = ClaimFactory.create(
            project__name="Test Project",
            project__start_date=date(2024, 1, 1),
            project__end_date=date(2024, 12, 31),
            period=date(2024, 1, 1),
            estimated_claim=100000.00,
        )
        expected = "Test Project - January 2024: R100000"
        assert str(claim) == expected

    def test_claim_period_normalization(self):
        """Test that period is normalized to first day of month."""
        project = ProjectFactory.create(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )
        claim = ClaimFactory.create(
            project=project,
            period=date(2024, 1, 15),  # Mid-month
            estimated_claim=100000.00,
        )
        # Should be saved as first day of month
        assert claim.period == date(2024, 1, 1)

    def test_claim_unique_per_project_period(self):
        """Test that claims must be unique per project and period."""
        project = ProjectFactory.create(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )
        period = date(2024, 1, 1)

        # Create first claim
        ClaimFactory.create(project=project, period=period, estimated_claim=100000.00)

        # Try to create duplicate claim
        with pytest.raises(ValidationError) as exc_info:
            ClaimFactory.create(
                project=project, period=period, estimated_claim=200000.00
            )

        assert "already exists" in str(exc_info.value)

    def test_claim_period_before_project_start(self):
        """Test validation when period is before project start date."""
        project = ProjectFactory.create(
            start_date=date(2024, 2, 1), end_date=date(2024, 12, 31)
        )

        with pytest.raises(ValidationError) as exc_info:
            ClaimFactory.create(
                project=project,
                period=date(2024, 1, 1),  # Before project start
                estimated_claim=100000.00,
            )

        assert "before project start date" in str(exc_info.value)

    def test_claim_period_after_project_end(self):
        """Test validation when period is after project end date."""
        project = ProjectFactory.create(
            start_date=date(2024, 1, 1), end_date=date(2024, 6, 30)
        )

        with pytest.raises(ValidationError) as exc_info:
            ClaimFactory.create(
                project=project,
                period=date(2024, 7, 1),  # After project end
                estimated_claim=100000.00,
            )

        assert "after project end date" in str(exc_info.value)

    def test_claim_negative_estimated_claim(self):
        """Test validation when estimated claim is negative."""
        project = ProjectFactory.create(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )

        with pytest.raises(ValidationError) as exc_info:
            claim = ClaimFactory.create(
                project=project, period=date(2024, 1, 1), estimated_claim=-100000.00
            )
            claim.full_clean()

        assert "greater than 0" in str(exc_info.value)

    def test_claim_zero_estimated_claim(self):
        """Test validation when estimated claim is zero."""
        project = ProjectFactory.create(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )

        with pytest.raises(ValidationError) as exc_info:
            claim = ClaimFactory.create(
                project=project, period=date(2024, 1, 1), estimated_claim=0
            )
            claim.full_clean()

        assert "greater than 0" in str(exc_info.value)

    def test_claim_ordering(self):
        """Test that claims are ordered by period descending."""
        project = ProjectFactory.create(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )

        # Create claims in chronological order
        claim1 = ClaimFactory.create(project=project, period=date(2024, 1, 1))
        claim2 = ClaimFactory.create(project=project, period=date(2024, 2, 1))
        claim3 = ClaimFactory.create(project=project, period=date(2024, 3, 1))

        # Query should return in reverse chronological order
        claims = list(project.claims.all())
        assert claims[0] == claim3
        assert claims[1] == claim2
        assert claims[2] == claim1

    def test_claim_soft_delete(self):
        """Test that claims are soft deleted."""
        project = ProjectFactory(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )
        # Create required items for project setup
        LineItemFactory.create_batch(3, project=project)
        PlannedValueFactory(project=project, period=date(2024, 1, 1))

        claim = ClaimFactory.create(project=project, period=date(2024, 2, 1))
        claim_id = claim.id

        # Soft delete the claim
        claim.soft_delete()

        # Should not appear in normal queries
        assert not Claim.objects.filter(id=claim_id).exists()

        # Should appear with all objects
        assert Claim.all_objects.filter(id=claim.id).exists()
        assert Claim.all_objects.get(id=claim.id).is_deleted is True

    def test_claim_restore(self):
        """Test that deleted claims can be restored."""
        project = ProjectFactory(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )
        # Create required items for project setup
        LineItemFactory.create_batch(3, project=project)
        PlannedValueFactory(project=project, period=date(2024, 1, 1))

        claim = ClaimFactory.create(project=project, period=date(2024, 2, 1))

        # Soft delete the claim
        claim.soft_delete()

        # Restore
        claim.restore()
        claim.refresh_from_db()

        assert claim.is_deleted is False
        assert claim.deleted is not None  # BaseModel keeps the timestamp

        # Should appear in normal queries again
        assert Claim.objects.filter(id=claim.id).exists()
