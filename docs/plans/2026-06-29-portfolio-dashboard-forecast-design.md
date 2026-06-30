# Design Document: Portfolio Dashboard Forecast Refactoring

Refactor the portfolio dashboard's Forecast at Completion and Estimate at Completion metrics to come from the project-level Earned Value (EVM) metrics.

## Background & Goal

Currently:
1. **Forecast at Completion** on the portfolio dashboard sums the approved forecasts from the `Forecast` model.
2. **Estimate at Completion (EAC)** on the portfolio dashboard delegates to the Forecast at Completion calculation, displaying the same value.
3. **Cost Variance at Completion** on the portfolio dashboard is computed as `Original Budget - Forecast at Completion`.

The goal is to update these portfolio-level metrics to aggregate project-level EVM metrics:
- **Forecast at Completion** should sum the projects' **Estimate to Complete (ETC)** (remaining cost).
- **Estimate at Completion** should sum the projects' **Estimate at Completion (EAC)** (total cost).
- **Cost Variance at Completion** should be `Original Budget - Estimate at Completion (EAC)`.

## Proposed Changes

We will modify two scopes where portfolio aggregation is defined:
1. The `Portfolio` model in [portfolio_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/models/portfolio_models.py) (used for regular users).
2. The `_PortfolioScope` helper class in [portfolio_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/views/portfolio_views.py) (used for staff/admin users).

### 1. Portfolio Model [portfolio_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/models/portfolio_models.py)

- Update `get_forecast_cost_at_completion` to sum `project.get_estimate_to_complete(date)`.
- Update `get_total_estimate_at_completion` to sum `project.get_estimate_at_completion(date)`.
- Update `get_cost_variance_at_completion` to compute `Original Budget - get_total_estimate_at_completion()`.

### 2. Admin Portfolio Scope [portfolio_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/views/portfolio_views.py)

- Update `_PortfolioScope.get_forecast_cost_at_completion` to sum `project.get_estimate_to_complete(date)`.
- Update `_PortfolioScope.get_total_estimate_at_completion` to sum `project.get_estimate_at_completion(date)`.
- Update `_PortfolioScope.get_cost_variance_at_completion` to compute `Original Budget - get_total_estimate_at_completion()`.

## Verification Plan

1. **Automated Tests**:
   - Create unit tests verifying the correctness of these aggregation methods on both `Portfolio` and `_PortfolioScope` under `app/Project/tests`.
   - Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/` to ensure all tests pass.

2. **Manual Verification**:
   - Verify the dashboard loads successfully and displays correct aggregated values for Forecast, EAC, and Cost Variance.
