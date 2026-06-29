# Portfolio Dashboard Forecast Refactoring Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Refactor the portfolio dashboard forecast and estimate at completion metrics to aggregate project-level EVM metrics (ETC and EAC).

**Architecture:** Update the financial aggregation methods in both the database model `Portfolio` and the local helper class `_PortfolioScope`.

**Tech Stack:** Python 3.13, Django 5.x, Pytest

---

### Task 1: Add PortfolioFactory to Project Factories

**Files:**
- Modify: `app/Project/tests/factories.py`

**Step 1: Write the minimal implementation**
Import `Portfolio` and define `PortfolioFactory` at the end of the file:
```python
from app.Project.models.portfolio_models import Portfolio

class PortfolioFactory(DjangoModelFactory):
    """Factory for Portfolio model."""

    class Meta:
        model = Portfolio
```

**Step 2: Run verification**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_portfolio_filters.py -v`
Expected: PASS

**Step 3: Commit**
```bash
git add app/Project/tests/factories.py
git commit -m "test: add PortfolioFactory to Project factories"
```

---

### Task 2: Create Unit Tests for Refactored Portfolio Metrics

**Files:**
- Create: `app/Project/tests/test_portfolio_metrics.py`

**Step 1: Write the failing tests**
Create tests that assert the correct aggregations of `etc` (for forecast), `eac` (for estimate), and `variance` (for cost variance) on both `Portfolio` and `_PortfolioScope`.
```python
import pytest
from decimal import Decimal
from datetime import datetime

from app.Project.models import Project
from app.Project.models.portfolio_models import Portfolio
from app.Project.views.portfolio_views import _PortfolioScope
from app.Project.tests.factories import ProjectFactory, PortfolioFactory

@pytest.mark.django_db
class TestPortfolioMetrics:
    """Test cases for refactored Portfolio and _PortfolioScope aggregation metrics."""

    def test_portfolio_evm_aggregations(self, monkeypatch):
        portfolio = PortfolioFactory.create()
        project1 = ProjectFactory.create(portfolio=portfolio, status="ACTIVE")
        project2 = ProjectFactory.create(portfolio=portfolio, status="ACTIVE")
        
        # Mock project level EVM values
        monkeypatch.setattr(Project, "get_estimate_to_complete", lambda self, date=None: Decimal("10000.00"))
        monkeypatch.setattr(Project, "get_estimate_at_completion", lambda self, date=None: Decimal("15000.00"))
        monkeypatch.setattr(Portfolio, "get_total_original_budget", lambda self, *args, **kwargs: Decimal("40000.00"))
        monkeypatch.setattr(_PortfolioScope, "get_total_original_budget", lambda self, *args, **kwargs: Decimal("40000.00"))
        
        # Test Portfolio model aggregation
        assert portfolio.get_forecast_cost_at_completion() == Decimal("20000.00") # ETC sum (10000 + 10000)
        assert portfolio.get_total_estimate_at_completion() == Decimal("30000.00") # EAC sum (15000 + 15000)
        assert portfolio.get_cost_variance_at_completion() == Decimal("10000.00") # Budget (40000) - EAC (30000)
        
        # Test _PortfolioScope helper aggregation
        scope = _PortfolioScope(portfolio.projects.all())
        assert scope.get_forecast_cost_at_completion() == Decimal("20000.00")
        assert scope.get_total_estimate_at_completion() == Decimal("30000.00")
        assert scope.get_cost_variance_at_completion() == Decimal("10000.00")
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_portfolio_metrics.py -v`
Expected: FAIL (methods not returning sum of ETC/EAC, or not implemented this way)

**Step 3: Commit**
```bash
git add app/Project/tests/test_portfolio_metrics.py
git commit -m "test: add unit tests for refactored portfolio metrics"
```

---

### Task 3: Implement Aggregations in Portfolio Model

**Files:**
- Modify: `app/Project/models/portfolio_models.py`

**Step 1: Write minimal implementation**
Refactor the following methods:
- `get_forecast_cost_at_completion`: sum `project.get_estimate_to_complete(date)`
- `get_total_estimate_at_completion`: sum `project.get_estimate_at_completion(date)`
- `get_cost_variance_at_completion`: compute `Original Budget - Estimate at Completion`

```python
    def get_forecast_cost_at_completion(
        self: "Portfolio",
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
        province: "Province | None" = None,
        area: "Municipality | None" = None,
        discipline: "ProjectDiscipline | None" = None,
    ) -> Decimal | None:
        """Sum of Estimate to Complete (ETC) for all active projects."""
        if not date:
            date = datetime.now()
        total = Decimal("0.00")
        valid_count = 0
        for project in self.get_active_projects(category, province, area, discipline):
            try:
                etc = project.get_estimate_to_complete(date)
                if etc is not None:
                    total += etc
                    valid_count += 1
            except (ZeroDivisionError, TypeError):
                continue
        return total if valid_count > 0 else None
```

```python
    def get_total_estimate_at_completion(
        self: "Portfolio",
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
        province: "Province | None" = None,
        area: "Municipality | None" = None,
        discipline: "ProjectDiscipline | None" = None,
    ) -> Decimal | None:
        """Sum of EAC for all active projects."""
        if not date:
            date = datetime.now()
        total = Decimal("0.00")
        valid_count = 0
        for project in self.get_active_projects(category, province, area, discipline):
            try:
                eac = project.get_estimate_at_completion(date)
                if eac is not None:
                    total += eac
                    valid_count += 1
            except (ZeroDivisionError, TypeError):
                continue
        return total if valid_count > 0 else None
```

```python
    def get_cost_variance_at_completion(
        self: "Portfolio",
        date: datetime | None = None,
        category: "ProjectCategory | None" = None,
        province: "Province | None" = None,
        area: "Municipality | None" = None,
        discipline: "ProjectDiscipline | None" = None,
    ) -> Decimal | None:
        """Original Budget - Estimate at Completion."""
        if not date:
            date = datetime.now()
        eac = self.get_total_estimate_at_completion(
            date, category, province, area, discipline
        )
        if not eac:
            return None
        return (
            self.get_total_original_budget(category, province, area, discipline) - eac
        )
```

**Step 2: Run test to verify it passes (Portfolio section)**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_portfolio_metrics.py -v`
Expected: Partial success (Portfolio passes, _PortfolioScope failing)

**Step 3: Commit**
```bash
git add app/Project/models/portfolio_models.py
git commit -m "feat: implement refactored metrics on Portfolio model"
```

---

### Task 4: Implement Aggregations in Admin Scope helper

**Files:**
- Modify: `app/Project/views/portfolio_views.py`

**Step 1: Write minimal implementation**
Refactor equivalent helper methods in `_PortfolioScope`:
- `get_forecast_cost_at_completion`
- `get_total_estimate_at_completion`
- `get_cost_variance_at_completion`

```python
            def get_forecast_cost_at_completion(
                self,
                date=None,
                category=None,
                province=None,
                area=None,
                discipline=None,
            ):
                if not date:
                    date = datetime.now()
                total = Decimal("0.00")
                valid_count = 0
                for project in self.get_active_projects(
                    category, province, area, discipline
                ):
                    try:
                        etc = project.get_estimate_to_complete(date)
                        if etc is not None:
                            total += etc
                            valid_count += 1
                    except (ZeroDivisionError, TypeError):
                        continue
                return total if valid_count > 0 else None
```

```python
            def get_total_estimate_at_completion(
                self,
                date=None,
                category=None,
                province=None,
                area=None,
                discipline=None,
            ):
                if not date:
                    date = datetime.now()
                total = Decimal("0.00")
                valid_count = 0
                for project in self.get_active_projects(
                    category, province, area, discipline
                ):
                    try:
                        eac = project.get_estimate_at_completion(date)
                        if eac is not None:
                            total += eac
                            valid_count += 1
                    except (ZeroDivisionError, TypeError):
                        continue
                return total if valid_count > 0 else None
```

```python
            def get_cost_variance_at_completion(
                self,
                date=None,
                category=None,
                province=None,
                area=None,
                discipline=None,
            ):
                eac = self.get_total_estimate_at_completion(
                    date, category, province, area, discipline
                )
                if not eac:
                    return None
                return (
                    self.get_total_original_budget(category, province, area, discipline)
                    - eac
                )
```

**Step 2: Run test to verify it passes (Both sections)**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_portfolio_metrics.py -v`
Expected: PASS

**Step 3: Commit**
```bash
git add app/Project/views/portfolio_views.py
git commit -m "feat: implement refactored metrics on _PortfolioScope helper"
```

---

### Task 5: Run Full Test Suite and Verification

**Files:**
- None (verification phase)

**Step 1: Run all tests**
Run: `.venv\Scripts\python.exe -m pytest`
Expected: PASS

**Step 2: Run code style checks**
Run: `.venv\Scripts\python.exe -m ruff check .`
Expected: PASS

**Step 3: Run code formatting**
Run: `.venv\Scripts\python.exe -m ruff format .`
Expected: PASS
