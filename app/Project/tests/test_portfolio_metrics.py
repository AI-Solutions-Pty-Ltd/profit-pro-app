from decimal import Decimal

import pytest

from app.Project.models import Project
from app.Project.models.portfolio_models import Portfolio
from app.Project.tests.factories import PortfolioFactory, ProjectFactory
from app.Project.views.portfolio_views import _PortfolioScope


@pytest.mark.django_db
class TestPortfolioMetrics:
    """Test cases for refactored Portfolio and _PortfolioScope aggregation metrics."""

    def test_portfolio_evm_aggregations(self, monkeypatch):
        portfolio = PortfolioFactory.create()
        _project1 = ProjectFactory.create(portfolio=portfolio, status="ACTIVE")
        _project2 = ProjectFactory.create(portfolio=portfolio, status="ACTIVE")

        # Mock project level EVM values
        monkeypatch.setattr(
            Project,
            "get_estimate_to_complete",
            lambda self, date=None: Decimal("10000.00"),
        )
        monkeypatch.setattr(
            Project,
            "get_estimate_at_completion",
            lambda self, date=None: Decimal("15000.00"),
        )
        monkeypatch.setattr(
            Portfolio,
            "get_total_original_budget",
            lambda self, *args, **kwargs: Decimal("40000.00"),
        )
        monkeypatch.setattr(
            _PortfolioScope,
            "get_total_original_budget",
            lambda self, *args, **kwargs: Decimal("40000.00"),
        )

        # Test Portfolio model aggregation
        assert portfolio.get_forecast_cost_at_completion() == Decimal(
            "20000.00"
        )  # ETC sum (10000 + 10000)
        assert portfolio.get_total_estimate_at_completion() == Decimal(
            "30000.00"
        )  # EAC sum (15000 + 15000)
        assert portfolio.get_cost_variance_at_completion() == Decimal(
            "10000.00"
        )  # Budget (40000) - EAC (30000)

        # Test _PortfolioScope helper aggregation
        scope = _PortfolioScope(portfolio.projects.all())
        assert scope.get_forecast_cost_at_completion() == Decimal("20000.00")
        assert scope.get_total_estimate_at_completion() == Decimal("30000.00")
        assert scope.get_cost_variance_at_completion() == Decimal("10000.00")
