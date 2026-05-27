# Superpowers Implementation Plan

## Goal
To implement a new non-expiring **Full Access** (`FULL_ACCESS`) subscription tier that allows authorized users full, unlimited module and role capability within their assigned projects and companies while preserving absolute multi-tenant data isolation.

## Assumptions
* The user's virtual environment `.venv` exists and Django environment is active.
* All permissions, decorators, and forms checking `has_demo_permission` will automatically inherit the `FULL_ACCESS` bypass since we will refactor `has_demo_permission` to return `True` for `FULL_ACCESS` users.
* A Django migration will be required to update the subscription field choices in the database.

---

## Plan

### 1. Add `FULL_ACCESS` to `Subscription` Choice Enum
* **Files:** [subscription_config.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/subscription_config.py)
* **Change:** 
  * Add the `FULL_ACCESS` key and description to the `Subscription` TextChoices class:
    ```python
    FULL_ACCESS = "FULL_ACCESS", "Full Access"
    ```
* **Verify:** Run the following command to check that `FULL_ACCESS` is registered in `Subscription`:
  ```bash
  .venv\Scripts\python.exe -c "from app.Account.subscription_config import Subscription; print(Subscription.FULL_ACCESS)"
  ```

### 2. Configure Limits for the `FULL_ACCESS` Tier
* **Files:** [subscription_config.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/subscription_config.py)
* **Change:**
  * Add the config limits mapping for `FULL_ACCESS` inside `SubscriptionConfig.LIMITS`:
    ```python
    Subscription.FULL_ACCESS: SubscriptionLimits(
        parent=Subscription.BUSINESS_MANAGEMENT,
        max_projects=50,
        max_users_per_project=100,
    ),
    ```
* **Verify:** Check limit extraction by running:
  ```bash
  .venv\Scripts\python.exe -c "from app.Account.subscription_config import Subscription, SubscriptionConfig; print(SubscriptionConfig.get_all_limits(Subscription.FULL_ACCESS))"
  ```

### 3. Implement Subscription and Project Role Bypass in `Account` Model
* **Files:** [models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/models.py)
* **Change:**
  * Update `has_subscription_tier` to instantly return `True` if `self.subscription == Subscription.FULL_ACCESS`.
  * Update `has_demo_permission` property to return `True` if the user is on the `FULL_ACCESS` tier (making it serve as a unified bypass property for active demo and full-access users alike):
    ```python
    @property
    def has_demo_permission(self) -> bool:
        """Check if the user has full access bypass (either active Demo or Full Access tier)."""
        from app.Account.subscription_config import Subscription

        return (
            self.subscription == Subscription.FULL_ACCESS
            or (
                self.subscription == Subscription.DEMO_TIER
                and not self.is_subscription_expired
            )
        )
    ```
* **Verify:** Run the current demo tier tests to ensure no regression was introduced:
  ```bash
  .venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py
  ```

### 4. Generate and Apply Database Migration
* **Files:** `app/Account/migrations/`
* **Change:**
  * Run Django's `makemigrations` to generate schema choice changes for the `Account.subscription` field.
  * Run `migrate` to apply the migrations to the database.
* **Verify:**
  ```bash
  .venv\Scripts\python.exe manage.py makemigrations Account
  .venv\Scripts\python.exe manage.py migrate Account
  ```

### 5. Write Comprehensive Unit Tests for the `FULL_ACCESS` Tier
* **Files:** [test_demo_tier.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/test_demo_tier.py)
* **Change:**
  * Add a new test class `TestFullAccessTier` implementing unit tests verifying that a `FULL_ACCESS` user:
    * Returns `True` for `has_demo_permission`.
    * Is never marked as expired (`is_subscription_expired` returns `False` even with past expiry dates or no expiry date).
    * Automatically satisfies `has_subscription_tier` checks for all core business management modules.
    * Bypasses project-level role restrictions for projects they are assigned to.
    * Only sees projects they are explicitly assigned to (ensuring strict multi-tenant boundary checks remain functional).
* **Verify:** Run the newly added test suite:
  ```bash
  .venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py -v
  ```

### 6. Verify Full System Suite Passes
* **Files:** Entire Project
* **Change:** None (Validation phase only)
* **Verify:** Run the entire test suite to ensure total system integrity:
  ```bash
  .venv\Scripts\python.exe -m pytest
  ```

---

## Risks & Mitigations
* **Risk:** The name `has_demo_permission` is slightly misleading once it covers `FULL_ACCESS`.
  * *Mitigation:* We add extensive, precise docstrings on the property describing exactly why both active `DEMO_TIER` and `FULL_ACCESS` satisfy the bypass. This avoids massive and risky multi-file refactoring.
* **Risk:** Accidental exposure of other users' projects/companies to `FULL_ACCESS` users.
  * *Mitigation:* Our implementation maintains the standard non-superuser lookup path for both `FULL_ACCESS` and `DEMO_TIER` users in `get_projects()` and client/consultant mixins. They remain strictly bounded to their assigned projects.

---

## Rollback Plan
* Discard changes using git:
  ```bash
  git checkout app/Account/subscription_config.py app/Account/models.py app/Account/tests/test_demo_tier.py
  ```
* Roll back the migration if it has been applied:
  ```bash
  .venv\Scripts\python.exe manage.py migrate Account <previous_migration_name>
  ```
* Remove the generated migration file from the filesystem.
