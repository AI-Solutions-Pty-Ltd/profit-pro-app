# Plan - Adding "demo 123" Project to Demo Tier Users as Read-Only

## Goal
Enable active `DEMO_TIER` users to dynamically see a project named "demo 123" in their project lists, while enforcing strict read-only access (GET/HEAD/OPTIONS permitted, write operations blocked) across all views and permission mixins.

## Assumptions
* Active demo-tier users are identified by the `has_demo_permission` property on `Account`.
* General write operations on demo projects are already blocked by checking `getattr(project, "is_demo", False)` in dispatch/permission mixins.
* Superusers/staff retain full read/write access to "demo 123" projects.

## Plan

### 1. Update Account Model Projects and Role Bypass Logic
* **Files**: [models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/models.py)
* **Change**:
  * In `get_projects`, dynamically include any project named `"demo 123"` if the user is in the `DEMO_TIER`.
  * In `has_project_role`, bypass role checks for projects named `"demo 123"` if the user has `has_demo_permission`.
* **Verify**:
  * Run `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py` to ensure existing demo tests pass.

### 2. Refactor View Queries to Leverage `get_projects`
* **Files**:
  * [project_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/project_views.py)
  * [portfolio_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/views/portfolio_views.py)
  * [project_role_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/views/project_role_views.py)
* **Change**:
  * In `ProjectMixin.get_queryset()`, use `self.request.user.get_projects.order_by("-created_at")` instead of the hardcoded `Q(users=self.request.user) | Q(is_demo=True)`.
  * In `PortfolioReportMixin.get_active_projects()`, use `self.request.user.get_projects` instead of the hardcoded queryset filter.
  * In `BaseRoleListView.get_project()`, `BaseRoleAddView.get_project()`, and `BaseRoleRemoveView.get_project()`, fetch projects from `self.request.user.get_projects` (or all projects if staff/superuser) instead of the hardcoded queryset.
* **Verify**:
  * Run Django check: `.venv\Scripts\python.exe manage.py check` to verify syntax and MRO.

### 3. Update Permission Mixins for Read-Only Scoping
* **Files**:
  * [permissions.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/core/Utilities/permissions.py)
  * [subscription_and_role_mixin.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/core/Utilities/subscription_and_role_mixin.py)
  * [subscriptions.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/core/Utilities/subscriptions.py)
  * [mixins.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/mixins.py)
* **Change**:
  * In `UserHasProjectRoleGenericMixin` (`permissions.py`), treat `project.name == "demo 123"` identically to `is_demo=True` for read-only checks.
  * In `SubscriptionAndRoleRequiredMixin` (`subscription_and_role_mixin.py`), treat `project.name == "demo 123"` identically to `is_demo=True` for read-only bypasses.
  * In `SubscriptionRequiredMixin` (`subscriptions.py`), treat `project.name == "demo 123"` identically to `is_demo=True` for read-only checks.
  * In `PaymentCertMixin.get_project()` (`mixins.py`), allow `DEMO_TIER` users to bypass consultant checks if `self.project.name == "demo 123"`.
* **Verify**:
  * Run `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py`

### 4. Implement Unit Tests for "demo 123" Project Scoping
* **Files**: [test_demo_tier.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/test_demo_tier.py)
* **Change**:
  * Implement `test_demo_123_visible_to_demo_tier_user` asserting "demo 123" is listed in active `DEMO_TIER` projects.
  * Implement `test_demo_123_not_visible_to_other_users` asserting "demo 123" is omitted from other user tiers.
  * Implement `test_demo_123_read_only_for_demo_tier_user` asserting read-only access (safe GETs pass, mutation POSTs/PUTs block).
* **Verify**:
  * Run `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py`

## Risks & mitigations
* **Risk**: High frequency database creation of "demo 123" inside standard tests might cause namespace collision.
  * *Mitigation*: Ensure "demo 123" is created dynamically inside unit tests via the `ProjectFactory` or query parameters and soft-deleted/cleaned up.
* **Risk**: Non-demo tier paid users might see "demo 123" if they share identical project query logic.
  * *Mitigation*: Explicitly check `self.subscription == Subscription.DEMO_TIER` when evaluating the "demo 123" project append in the model.

## Rollback plan
* Restore modified files from git HEAD (`git checkout -- <filepath>`) to revert any query modifications.
