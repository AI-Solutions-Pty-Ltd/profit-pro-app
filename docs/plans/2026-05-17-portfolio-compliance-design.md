# Master Portfolio Dashboard - Compliance Aggregation Design

## Overview
The goal is to update the Master Portfolio Dashboard's "Project Stats" section to display the number of *projects* experiencing cost/schedule overruns and compliance issues (Correspondence, Safety, Quality) rather than the raw sum of activities or items across the portfolio. 

## Approach
Context-Aware Backend Aggregation (Approach 1)

## Implementation Details

1. **Backend (`MasterDashboardDataMixin` in `company_views.py`)**:
   - Inside `_get_compliance_summary`, check if `projects.count() > 1`.
   - If `True` (Portfolio Mode):
     - `pending_rfis` = `RFI.objects.filter(project__in=projects, status=RFIStatus.OPEN, deleted=False).values('project').distinct().count()`
     - `quality_matters` = `NonConformance.objects.filter(project__in=projects, type=NonConformanceType.QUALITY, status=NCRStatus.OPEN, deleted=False).values('project').distinct().count()`
     - `safety_matters` = `Incident.objects.filter(project__in=projects, status=IncidentStatus.OPEN, deleted=False).values('project').distinct().count()`
     - Pass an `issue_type` context variable (e.g. `"Projects"` vs `"Items"`).
   - If `False` (Project Mode):
     - Fallback to standard `.count()` queries to show exact incident totals.
     - Set `issue_type = "Items"`.
   - Ensure the "Total Active Number" uses `project_count` from context.

2. **Frontend (`_summary_stats.html`)**:
   - Update text labels to be dynamic based on the context.
   - For Cost and Schedule overruns: `{{ production.overrun_type }} with cost overruns`.
   - For Correspondence, Safety, Quality: `{{ compliance.issue_type }} with pending matters`.

## Validation
- Verify "Total Active Number" accurately reflects the number of active projects in the portfolio view.
- Ensure compliance sections correctly render the project count when in Portfolio view, but the item count when in a single Project view.
