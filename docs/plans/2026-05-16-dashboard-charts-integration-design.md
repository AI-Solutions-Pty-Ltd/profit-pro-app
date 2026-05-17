# Design: Unified Dashboard Charts Integration

## Goal
Integrate dynamic, aggregated "Trajectory Analysis" (S-Curve) and "Net Profit Trend" charts into both the Master Project Dashboard and the Master Portfolio Dashboard.

## Components

### 1. Data Aggregator Update (`production_utils.py`)
- **Function**: `get_project_productivity_report_data`
- **Change**: Modify to accept a queryset of projects instead of a single ID.
- **Logic**: 
    - Sum daily planned/actual metrics across all projects.
    - Calculate cumulative series for the combined dataset.
    - Return `charts_json` suitable for multi-chart rendering.

### 2. Dashboard View Mixin (`company_views.py`)
- **Function**: `MasterDashboardDataMixin.get_master_context`
- **Integration**: Invoke the updated aggregator for the current project scope.
- **Context**: Add `charts_json` to the returned dictionary.

### 3. Shared Partial (`_dashboard_charts.html`)
- **Path**: `app/Project/templates/company/partials/master_dashboard/_dashboard_charts.html`
- **Content**: 
    - `accumulationChart` canvas.
    - `profitChart` canvas.
    - Shared `Chart.js` initialization script.

### 4. Layout Updates
- **Project Dashboard**: Replace legacy mocked charts with the new partial.
- **Portfolio Dashboard**: Replace legacy mocked charts with the new partial.

## Verification Plan
- **Single Project**: Verify charts match the Performance Report for that project.
- **Portfolio**: Verify charts correctly sum data from all active projects in the portfolio.
