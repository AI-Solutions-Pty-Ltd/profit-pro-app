# Brainstorming: Adding "demo 123" Project to Demo Tier Users as Read-Only

This document details the goals, constraints, context, risks, options, and recommended approach for enabling a dedicated "demo 123" project for all demo-tier users under read-only restrictions.

---

## Goal
* Dynamically present a project named "demo 123" in the project and portfolio lists of all active `DEMO_TIER` users.
* Enforce strict read-only access (GET/HEAD/OPTIONS allowed; POST/PUT/DELETE/PATCH blocked) for demo tier users accessing "demo 123".

## Constraints
* **Virtual Environment**: All validations, commands, and dependencies must run inside the `.venv` development environment.
* **Test Discipline**: Must use `factory_boy` factories for testing and avoid raw ORM creations in test files.
* **Base Models**: Custom models must inherit from `app.core.Utilities.models.BaseModel`.
* **Read-Only Rigor**: Any attempt by a demo tier user to modify "demo 123" (e.g., uploading WBS, creating a payment certificate) must fail with a 403 response or a read-only redirect/error message.

## Known context
* **Demo Permission Hook**: Active demo-tier users are identified by the `has_demo_permission` property (returns `True` if `subscription == DEMO_TIER` and is not expired).
* **Project Querying**: Users get their project list via the `get_projects` property on the `Account` model. However, several mixins and report views hardcode project queryset logic as `Q(users=self.request.user) | Q(is_demo=True)`.
* **Read-Only Enforcement**: Read-only enforcement for demo projects is handled at the mixin level in `app/core/Utilities/permissions.py` (checks `getattr(project, "is_demo", False)`).
* **Role Bypasses**: Active demo tier users automatically bypass project role checks (`has_project_role` returns `True`) for `is_demo=True` projects.

## Risks
* **Data Isolation Leak**: If "demo 123" is marked as `is_demo = True`, it automatically becomes visible to all tiers (e.g. `FREE_TIER`, standard paid tiers). If we want it restricted specifically to `DEMO_TIER` users, using `is_demo = True` alone is insufficient.
* **Inconsistent View Support**: Hardcoded querysets in mixins or report views (such as `ProjectMixin.get_queryset` and `PortfolioReportMixin.get_active_projects`) will omit "demo 123" if they only check `is_demo=True` or explicit user assignments.
* **Mutation Vulnerability**: Failing to align all custom mixins (e.g. `SubscriptionAndRoleRequiredMixin`, `SubscriptionRequiredMixin`, `PaymentCertMixin`) could allow write actions on "demo 123".

## Options (2???4)

### Option 1: Explicit Database Seeding and Scoped Assignment
* **Description**: Create a migration or post-save signal that ensures a project named "demo 123" (with `is_demo=False`) exists in the database. When a `DEMO_TIER` user is created, explicitly add them to the project's ManyToMany `users` field. Enforce read-only logic in permission mixins specifically by checking `project.name == "demo 123"`.
* **Pros**: No changes needed for `get_projects` queryset logic; standard project associations work natively.
* **Cons**: High database overhead. Deleting or cleaning expired demo accounts requires extra cleanup steps. Difficult to scale if thousands of demo users are registered.

### Option 2: Dynamic QuerySet Injection and Unified Mixin Treatment (Recommended)
* **Description**:
  1. Dynamically append "demo 123" to the `get_projects` QuerySet for active `DEMO_TIER` users.
  2. Refactor all hardcoded querysets in `ProjectMixin.get_queryset` and `PortfolioReportMixin.get_active_projects` to utilize the `user.get_projects` property directly, promoting DRY principles.
  3. Update permission mixins (`UserHasProjectRoleGenericMixin`, `SubscriptionAndRoleRequiredMixin`, `SubscriptionRequiredMixin`, `PaymentCertMixin`) and the `Account.has_project_role` method to treat `project.name == "demo 123"` identically to `is_demo=True` projects (read-only for non-staff).
* **Pros**: 
  * Clean, fully dynamic, and zero database management/cleanup overhead.
  * Ensures perfect tier isolation (only `DEMO_TIER` and staff/superusers can see it).
  * Automatically propagates across all views and report summaries.
* **Cons**: Requires refactoring of hardcoded project querysets in views.

---

## Recommendation
Implement **Option 2**. It provides an elegant, scalable, and secure solution that leverages the existing `get_projects` property and read-only mixin structures, while correcting several hardcoded query anomalies across the codebase.

---

## Acceptance criteria
1. **Visibility**:
   * Active `DEMO_TIER` users see the "demo 123" project in their project lists and portfolio dashboards.
   * `FREE_TIER` and other non-demo/non-staff users cannot see or access "demo 123".
   * Superusers and staff can see and fully manage "demo 123".
2. **Access Control**:
   * Active `DEMO_TIER` users can successfully view all dashboard pages, BOQ/WBS items, and compliance/payment certificate records of the "demo 123" project.
   * Active `DEMO_TIER` users are strictly blocked from writing, updating, or deleting any records within "demo 123", returning a `403 Forbidden` response or redirection with a "read-only" error message.
3. **Tests**:
   * Comprehensive unit tests are added to verify visibility, access control, and mutation blocks on "demo 123" projects.
   * Entire pytest suite runs and passes successfully.
