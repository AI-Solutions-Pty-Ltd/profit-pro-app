from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from app.Project.profitability.mixins import FinancialCalculationMixin
from app.Project.profitability.tests.factories import ProfitabilityBaselineFactory
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestProfitabilityBaseline:
    """Test cases for ProfitabilityBaseline model and its impact on mixins."""

    def test_baseline_creation(self):
        """Test creating a baseline with valid data."""
        baseline = ProfitabilityBaselineFactory(
            cost_of_sales_percent=50.0,
            operating_expenses_percent=20.0,
            net_profit_percent=30.0,
        )
        assert baseline.id is not None
        assert baseline.cost_of_sales_percent == Decimal("50.00")
        assert baseline.operating_expenses_percent == Decimal("20.00")
        assert baseline.net_profit_percent == Decimal("30.00")

    def test_baseline_validation_fails(self):
        """Test that validation fails if percentages do not sum to 100%."""
        baseline = ProfitabilityBaselineFactory(
            cost_of_sales_percent=50.0,
            operating_expenses_percent=20.0,
            net_profit_percent=20.0,  # Total = 90
        )
        with pytest.raises(ValidationError):
            baseline.full_clean()

    def test_mixin_uses_db_values(self):
        """Test that FinancialCalculationMixin uses values from the DB if they exist."""
        project = ProjectFactory()
        ProfitabilityBaselineFactory(
            project=project,
            cost_of_sales_percent=55.0,
            operating_expenses_percent=15.0,
            net_profit_percent=30.0,
        )

        class MockReportView(FinancialCalculationMixin):
            def __init__(self, project):
                self.project = project

        view = MockReportView(project)
        assumptions = view.get_baseline_assumptions()

        assert assumptions["cost_of_sales_percent"] == 55.0
        assert assumptions["operating_expenses_percent"] == 15.0
        assert assumptions["net_profit_percent"] == 30.0

    def test_mixin_uses_defaults_if_no_db_record(self):
        """Test that FinancialCalculationMixin falls back to defaults if no record exists."""
        project = ProjectFactory()

        class MockReportView(FinancialCalculationMixin):
            def __init__(self, project):
                self.project = project

        view = MockReportView(project)
        assumptions = view.get_baseline_assumptions()

        assert assumptions["cost_of_sales_percent"] == 60.0
        assert assumptions["operating_expenses_percent"] == 12.0
        assert assumptions["net_profit_percent"] == 28.0
