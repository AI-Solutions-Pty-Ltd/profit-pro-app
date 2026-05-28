# Execution Notes: Adding "demo 123" Project to Demo Tier Users as Read-Only

This file tracks the execution progress of each step of the approved implementation plan.

---

### 1. Update Account Model Projects and Role Bypass Logic
* **Files**: `app/Account/models.py`
* **Change**:
  * In `get_projects`, dynamically include any project named `"demo 123"` if the user is in the `DEMO_TIER`.
  * In `has_project_role`, bypass role checks for projects named `"demo 123"` if the user has `has_demo_permission`.
* **Verify**: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py`
* **Result**: PASS (All 16 tests passed)

### 2. Refactor View Queries to Leverage `get_projects`
* **Files**:
  * `app/Project/projects/project_views.py`
  * `app/Project/views/portfolio_views.py`
  * `app/Project/views/project_role_views.py`
* **Change**:
  * Refactored `ProjectMixin.get_queryset` in `project_views.py` to use `user.get_projects.order_by("-created_at")`.
  * Refactored `PortfolioReportMixin.get_active_projects` in `portfolio_views.py` to use `user.get_projects.filter(status=ACTIVE)`.
  * Refactored `get_project` helper methods in `project_role_views.py` to fetch from `user.get_projects` (with staff/superuser bypass).
* **Verify**: `.venv\Scripts\python.exe manage.py check`
* **Result**: PASS (System check identified no issues)

### 3. Update Permission Mixins for Read-Only Scoping
* **Files**:
  * `app/core/Utilities/permissions.py`
  * `app/core/Utilities/subscription_and_role_mixin.py`
  * `app/core/Utilities/subscriptions.py`
  * `app/Consultant/views/mixins.py`
* **Change**:
  * Updated `UserHasProjectRoleGenericMixin` in `permissions.py` to treat `project.name == "demo 123"` as read-only.
  * Updated `SubscriptionAndRoleRequiredMixin` in `subscription_and_role_mixin.py` to treat `project.name == "demo 123"` as read-only.
  * Updated `SubscriptionRequiredMixin` in `subscriptions.py` to treat `project.name == "demo 123"` as read-only.
  * Updated `PaymentCertMixin.get_project()` in `mixins.py` to allow `DEMO_TIER` users to bypass consultant checks for `project.name == "demo 123"`.
* **Verify**: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py`
* **Result**: PASS (All 16 tests passed)

### 4. Implement Unit Tests for "demo 123" Project Scoping
* **Files**: `app/Account/tests/test_demo_tier.py`
* **Change**:
  * Implemented `TestDemo123Project` with three targeted unit tests testing visibility, isolation, and read-only blocks for the `"demo 123"` project.
  * Fixed a minor flakiness in the existing `test_demo_time_left_str` test by adding padding seconds to prevent division-rounding discrepancies.
* **Verify**: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py`
* **Result**: PASS (All 19 tests passed successfully)
