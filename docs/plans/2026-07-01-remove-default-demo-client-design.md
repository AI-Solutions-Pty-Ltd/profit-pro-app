# Design Specification: Remove Default Demo Client from Approval List and Forms

This document specifies the design to remove the global default "Demo Client" company (with registration number `DEMO-CLIENT`) from the consultant approval list and project-related forms for users on the Demo subscription tier.

## Goals
1. **Clean Separation**: Prevent the global default "Demo Client" from appearing in the consultant's list of assigned clients ("approval list").
2. **Consistent Filtering**: Remove the global "Demo Client" from form selection options (`ProjectClientForm`) and project filter dropdowns (`ProjectFilterForm`) so that demo users only interact with their own user-scoped demo clients.

---

## Proposed Changes

### 1. Consultant Views Mixin
**File**: [mixins.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/mixins.py)
* In `ConsultantMixin.get_clients()`, remove the query condition `Q(name="Demo Client")`. This ensures that active trial demo users only see clients they are explicitly associated with (via consultants, users, or projects).

### 2. Project Client Form
**File**: [forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/forms.py)
* In `ProjectClientForm.__init__()`, update the condition list for demo permissions to only include the user-scoped demo client:
  ```python
  registration_number__in=[f"DEMO-CLIENT-{user.pk}"]
  ```

### 3. Project Filter Form
**File**: [project_forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/project_forms.py)
* In `ProjectFilterForm.__init__()`, update the demo client filtering query to exclude `"DEMO-CLIENT"`:
  ```python
  registration_number__in=[f"DEMO-CLIENT-{user.pk}"]
  ```

---

## Verification Plan

### Automated Tests
Run the test suites to ensure behavior changes and existing code still passes:
* `.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_demo_tier_consultant.py`
* `.venv\Scripts\python.exe -m pytest app/Project/tests/test_demo_companies.py`
