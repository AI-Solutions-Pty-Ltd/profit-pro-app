# Superpowers Brainstorm

## Goal
The goal is to create a new non-expiring **Full Access** subscription tier, similar in capability to the existing `DEMO_TIER`. This tier will grant a user full module and project role access within the projects and client/contractor companies they are associated with, while strictly ensuring they cannot see or modify unrelated data from other users or projects (preserving standard data isolation and tenant boundary constraints).

## Constraints
1. **Existing Architecture Alignment:** The new tier must be seamlessly integrated into the existing `Subscription` choices enum and `SubscriptionConfig.LIMITS`.
2. **Data Privacy (Tenant Isolation):** Standard data isolation must remain intact. Users on this tier are *not* superusers and must only see projects they are explicitly added to, and only clients/contractors associated with those projects.
3. **No Automatic Expiry:** Unlike `DEMO_TIER` which expires after 7 days (or standard trial periods), this tier must not automatically expire or be blocked by trial lockout middleware.
4. **Clean Code and Maintainability:** Avoid duplicating permission logic. We should unify the project role/group bypass logic currently used for `DEMO_TIER` with this new tier.
5. **Standards Compliance:** All code must conform to Python 3.13+, Ruff styling guidelines, and pass all system tests without introducing regressions.

## Known Context
* **Tiers & Subscriptions:** Defined in `app/Account/subscription_config.py`.
* **Project Role Bypass:** Currently, active demo users (`has_demo_permission`) bypass the project role permission checks in `Account.has_project_role()`, `UserHasProjectRoleGenericMixin`, and various forms/views.
* **Group Permission Bypass:** Demo users bypass Django group permission checks via `UserHasGroupGenericMixin`.
* **Standard Filtering:** `Account.get_projects` and mixins like `ConsultantMixin.get_clients` check `self.is_superuser` to determine whether to return all data vs. filtering to only associated items. For non-superusers (including demo users), it uses strict filtering.

## Risks
* **Privilege Escalation / Data Leaking:** If the implementation makes full-access users behave like superusers (e.g. bypassing the `is_superuser` checks in `get_projects` or `get_clients`), they would see other users' private data. We must ensure the new tier inherits the standard filter behavior, *not* the superuser bypass.
* **Middleware Expiration Check:** We must ensure the demo lockout middleware (`demo_expired_middleware.py`) does not flag or block users on the new non-expiring tier.
* **Migration Integrity:** Adding a choice to `Subscription` requires creating a Django migration to update the field choices in the database safely.

## Options (2–4)

### Option A: Clean Extension with Unified Bypass (Recommended)
1. Add `FULL_ACCESS = "FULL_ACCESS", "Full Access"` to the `Subscription` enum.
2. Configure limits for `FULL_ACCESS` in `SubscriptionConfig.LIMITS` (matching `DEMO_TIER` limits but with no expiry check).
3. Introduce a unified property `has_full_access_bypass` on the `Account` model:
   ```python
   @property
   def has_full_access_bypass(self) -> bool:
       """Check if the user has full access bypass (either active Demo or Full Access tier)."""
       return (
           self.subscription == Subscription.FULL_ACCESS
           or self.has_demo_permission
       )
   ```
4. Update all core permission/bypass checks (including `has_project_role`, template tags, form classes, and mixins) to check `has_full_access_bypass` instead of `has_demo_permission`.
5. Write unit tests verifying full access permissions, data isolation, and lack of expiration.

### Option B: Reuse `ADMINISTRATION` Tier and Enable Project-Role Bypass
1. Modify the existing `ADMINISTRATION` tier's definition.
2. Currently, the `ADMINISTRATION` tier acts as full access in terms of subscriptions but is *not* granted the project-role/group bypass that `DEMO_TIER` has.
3. We could update `has_demo_permission` or project role checks to include `self.subscription == Subscription.ADMINISTRATION`.

### Option C: Decouple Via a Boolean Attribute on Account
1. Add a new database column `is_full_access` (boolean) to the `Account` model.
2. Bypass role/subscription checks if `is_full_access` is `True`.

## Recommendation
We strongly recommend **Option A**. It leverages the clean, existing subscription engine, introduces zero architectural bloat, and provides an extremely readable and maintainable way to manage high-tier users who need full capabilities within their own workspace without experiencing trial expiration.

## Acceptance Criteria
1. **Tier Definition:** `Subscription` choices enum contains `FULL_ACCESS` ("Full Access").
2. **Subscription Config:** `FULL_ACCESS` limits are configured in `SubscriptionConfig.LIMITS`.
3. **Graceful Bypass:** A user on the `FULL_ACCESS` tier has all modules/features unlocked and bypasses standard project-level roles (just like `DEMO_TIER`), but does *not* expire.
4. **Data Isolation:** `FULL_ACCESS` users cannot see projects, clients, or data that they are not explicitly associated with.
5. **Lockout Safety:** The new tier is completely unaffected by trial expiry logic or lockout middleware.
6. **Robust Testing:** Unit tests exist verifying active `FULL_ACCESS` users can view their own data, pass permission checks, and do not expire.
7. **Database Migration:** A Django schema migration is generated and applied successfully.
