# Superpowers Brainstorm

## Goal
Make `FULL_ACCESS` the default subscription tier when creating a new `Account` user.

## Constraints
* **Existing Codebase Harmony:** Ensure the default choice matches the `Subscription` choices enum seamlessly.
* **Test Suite Correctness:** Update unit tests that explicitly assert that newly created accounts default to `DEMO_TIER`, while ensuring existing `DEMO_TIER` tests still run correctly by explicitly passing `subscription=Subscription.DEMO_TIER` where necessary.
* **Migration Integration:** Generate and apply a new Django migration that updates the `default` value of the `subscription` column on the database level.
* **Ruff Compliance:** Keep code formatted and clean according to Ruff guidelines.

## Known Context
* In `app/Account/models.py`, the `Account.subscription` field has `default=Subscription.DEMO_TIER`.
* In `app/Account/tests/test_models.py`, `TestAccountSubscription.test_default_subscription_is_demo` asserts that a new account defaults to `DEMO_TIER`.
* In `app/Account/tests/factories.py`, `AccountFactory` and `UserFactory` comments refer to utilizing the model default `DEMO_TIER`.
* Newly created accounts are added to the default `contractor` group and if they are demo tier, their expiry is calculated by the signal in `app/Account/signals.py`. If they are `FULL_ACCESS`, no expiry will be set, which matches the required non-expiring behavior.

## Risks
* **Broken Tests:** Changing the default tier may cause tests that assumed newly created users are on `DEMO_TIER` (and therefore are subject to lockout or are trials) to fail or behave differently.
  * *Mitigation:* Carefully audit all `pytest` errors after changing the default. Update `test_models.py` to assert default to `FULL_ACCESS`, and verify if other test classes (like `test_create_demo_user.py` or `test_demo_lockout.py`) specifically expect `DEMO_TIER` defaults. (Most of them use factories or create a demo user command which explicitly sets the subscription to `DEMO_TIER`, so they should remain safe).
* **Database Default Out of Sync:** Failing to run migration leaves the database default out of sync with the Django model class definition.
  * *Mitigation:* Always generate (`makemigrations`) and apply (`migrate`) the changes immediately using the virtual environment.

## Options (2–4)

### Option 1: Direct model default update + update default-asserting tests (Recommended)
Directly change the `default` on the `Account.subscription` field in `models.py` from `Subscription.DEMO_TIER` to `Subscription.FULL_ACCESS`. Update `test_models.py` and `factories.py` to reflect this change, run migrations, and execute all tests.
* *Pros:* Simple, direct, correct, aligns perfectly with Django design patterns.
* *Cons:* Requires updating a few assertions in `test_models.py`.

### Option 2: Keep model default as `DEMO_TIER` and default to `FULL_ACCESS` in UserManager / create_user
Keep the default on the model field as `DEMO_TIER` but intercept user creation inside `UserManager.create_user()` to set `subscription` to `FULL_ACCESS` if not explicitly specified.
* *Pros:* Preserves some database-level field settings.
* *Cons:* Confusing, prone to errors if users are created through other Django operations (like admin panel, `Account.objects.create()`, or custom commands) that bypass the manager method, violating database integrity.

---

## Recommendation
We recommend **Option 1**. It is the standard, clean, and most maintainable Django paradigm. It ensures that any user created via any channel (Django Admin, shell, factory, or standard signup) consistently receives the `FULL_ACCESS` default.

---

## Acceptance Criteria
1. **Model Default Update:** The `Account.subscription` field default value is set to `Subscription.FULL_ACCESS` in `app/Account/models.py`.
2. **Database Choice Schema Alignment:** A Django database migration is generated and successfully applied to update the field default.
3. **Factories & Documentation Updated:** `app/Account/tests/factories.py` comments/defaults are updated to reflect the new default tier.
4. **Assert Correct Default in Test:** `TestAccountSubscription.test_default_subscription_is_demo` in `test_models.py` is renamed/updated to assert default to `FULL_ACCESS` and passes.
5. **No Regressions:** All existing 70 tests in `app/Account/tests/` and related app tests pass without issue.
