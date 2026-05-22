# Design Specification: Central Demo Permission & Subscription Verification

This specification outlines the architecture, model updates, view permission mixins refactoring, template checks, and validation suites to introduce a centralized `has_demo_permission` property in the Profit Pro Django application.

## Goals
1. **Centralize Trial Logic**: Eliminate repeated inline queries that evaluate whether a user's trial is active or expired.
2. **Prevent Expired Trial Bypasses**: Ensure all views, templates, navigation components, and custom template filters consistently respect the subscription expiration status of the Demo Tier.
3. **Upgrade Path CTA**: Keep the sticky header/ribbon visible for expired trials to act as a clear conversion point for purchasing the full app.

---

## Architectural Approach

We will define `has_demo_permission` directly on the custom `Account` model as a dynamic property.
* This property returns `True` if and only if the user's subscription tier is `DEMO_TIER` and `is_subscription_expired` evaluates to `False`.
* Base permission mixins (`UserHasGroupGenericMixin`), specialist views mixins (`ConsultantMixin`, `PaymentCertMixin`), template tags, and dashboards will consume this single property.

---

## Technical Specifications

### 1. Model Updates (`app/Account/models.py`)
* **Dynamic Property**: Add `has_demo_permission` on `Account` class:
  ```python
  @property
  def has_demo_permission(self) -> bool:
      """Check if the user has an active, unexpired Demo subscription."""
      from app.Account.subscription_config import Subscription
      return self.subscription == Subscription.DEMO_TIER and not self.is_subscription_expired
  ```
* **Bypass logic cleanups**:
  * In `has_subscription_tier()`, check:
    ```python
    if self.subscription == Subscription.DEMO_TIER:
        return not self.is_subscription_expired
    ```
  * In `has_project_role()`, use the property:
    ```python
    if self.is_superuser or self.has_demo_permission:
        return True
    ```

### 2. Base & Specialized Permission Mixins
* **File**: `app/core/Utilities/permissions.py`
  * In `UserHasGroupGenericMixin.test_func()`, check `getattr(self.request.user, "has_demo_permission", False)`.
* **File**: `app/Consultant/views/mixins.py`
  * In `ConsultantMixin.get_clients()`, check `getattr(self.request.user, "has_demo_permission", False)`.
  * In `PaymentCertMixin.get_project()`, check `getattr(user, "has_demo_permission", False)`.

### 3. Template Tag Filters
* **File**: `app/core/templatetags/template_extras.py`
  * In `project_roles()`, substitute manual inline `DEMO_TIER` checks with:
    ```python
    if user.is_superuser or getattr(user, "has_demo_permission", False):
        from app.Project.models import ProjectRole
        return ProjectRole.objects.all()
    ```

### 4. Template-Level Checks
* **File**: `app/templates/nav.html`
  * Replace `user.subscription == 'DEMO_TIER'` with `user.has_demo_permission` on critical links (e.g. lines 67, 83) so restricted features disappear upon expiration.
  * Retain `user.subscription == "DEMO_TIER"` for the banner container at line 3 to ensure the Call to Action ribbon stays visible with an **Expired** countdown message when the trial lapses.
* **File**: `app/Project/templates/project/project_setup.html`
  * Replace standard manual subscription comparisons with `user.has_demo_permission`.

---

## Verification Plan

### Automated Verification
Add the following target test cases to `app/Account/tests/test_demo_tier.py`:
* `test_has_demo_permission_active`: Returns `True` when subscription is `DEMO_TIER` and expiration is in the future.
* `test_has_demo_permission_expired`: Returns `False` when subscription is `DEMO_TIER` and expiration has passed.
* `test_has_demo_permission_other_tier`: Returns `False` for other active/expired tiers.
* `test_has_demo_permission_no_expiry`: Returns `False` gracefully if `subscription_expires_at` is `None`.

Command to execute tests:
```bash
.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py -v
```

### Manual Verification
* Change developer account to `DEMO_TIER` with future date, verify Dashboard/Consultant components load normally.
* Move the expiration date to 1 hour in the past, verify the navigation links are hidden, the ribbon shows **Expired**, and direct page accesses trigger redirects.
