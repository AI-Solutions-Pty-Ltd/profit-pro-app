# Superpowers Implementation Plan

## Goal
Set `FULL_ACCESS` as the default subscription tier when creating a user, both in the model schema definition and across all associated tests, factories, and database migrations.

## Assumptions
* The user's virtual environment `.venv` exists and Django environment is active.
* Standard data isolation and permissions rules still apply, meaning a user defaulting to `FULL_ACCESS` receives non-expiring full project-scope access by default.

---

## Plan

### 1. Update Default Subscription in `Account` Model
* **Files:** [models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/models.py)
* **Change:**
  * Update `Account.subscription` field `default` property from `Subscription.DEMO_TIER` to `Subscription.FULL_ACCESS`.
* **Verify:**
  * Run Ruff check: `.venv\Scripts\python.exe -m ruff check app/Account/models.py`

### 2. Generate and Apply Database Migration
* **Files:** `app/Account/migrations/`
* **Change:**
  * Run `makemigrations` to generate the default value update for the `Account.subscription` field.
  * Run `migrate` to apply the migration to the active database.
* **Verify:**
  * `.venv\Scripts\python.exe manage.py makemigrations Account`
  * `.venv\Scripts\python.exe manage.py migrate Account`

### 3. Update Factories Documentation/Comments
* **Files:** [factories.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/factories.py)
* **Change:**
  * Update comments referring to the model default in `UserFactory` and `AccountFactory` from `# Use model default (DEMO_TIER)` to `# Use model default (FULL_ACCESS)`.
* **Verify:**
  * Run Ruff check: `.venv\Scripts\python.exe -m ruff check app/Account/tests/factories.py`

### 4. Update and Rename Subscription Default Test
* **Files:** [test_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/test_models.py)
* **Change:**
  * Rename `test_default_subscription_is_demo` to `test_default_subscription_is_full_access` and update the assertion to assert `account.subscription == Subscription.FULL_ACCESS`.
* **Verify:**
  * Run the `test_models.py` test suite: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_models.py`

### 5. Audit and Verify Entire Account Test Suite
* **Files:** Entire Account tests folder
* **Change:** None (Verification phase only)
* **Verify:**
  * Run the complete Account test suite to ensure no other tests depend on the old default:
    `.venv\Scripts\python.exe -m pytest app/Account/tests/`

---

## Risks & Mitigations
* **Risk:** Other apps or test suites might implicitly rely on new users defaulting to `DEMO_TIER` for trial timing or demo lockout assertions.
  * *Mitigation:* Running the full Account test suite will instantly highlight any such tests. We will explicitly pass `subscription=Subscription.DEMO_TIER` to factories in those specific test cases if needed.

---

## Rollback Plan
* Discard changes using git:
  `git checkout app/Account/models.py app/Account/tests/factories.py app/Account/tests/test_models.py`
* Rollback the migration:
  `.venv\Scripts\python.exe manage.py migrate Account <previous_migration>` and delete the new migration file.
