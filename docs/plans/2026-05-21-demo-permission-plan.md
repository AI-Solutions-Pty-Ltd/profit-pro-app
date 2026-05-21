# Central Demo Permission Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Create a centralized, dynamic `has_demo_permission` property on the `Account` model and update all permission mixins, template tags, and HTML pages to eliminate trial bypasses for expired demo accounts.

**Architecture:** We will define `Account.has_demo_permission` on the custom user model to encapsulate `subscription == Subscription.DEMO_TIER and not is_subscription_expired`. This property will act as the single source of truth, used in Python permission checks, template tags, and conditional blocks in templates.

**Tech Stack:** Python 3.13+, Django 5.0.4, Pytest, factory_boy.

---

### Task 1: Account Model Updates & Dynamic Property Tests

**Files:**
- Modify: `app/Account/models.py`
- Test: `app/Account/tests/test_demo_tier.py`

**Step 1: Write the failing tests**
Add new test cases to `app/Account/tests/test_demo_tier.py` verifying the `has_demo_permission` property behavior under active, expired, other subscription tiers, and `None` expiry conditions.

```python
    def test_has_demo_permission_active(self):
        """Test that has_demo_permission is True for active trials."""
        expiry = timezone.now() + timedelta(days=5)
        user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=expiry,
        )
        assert user.has_demo_permission is True

    def test_has_demo_permission_expired(self):
        """Test that has_demo_permission is False for expired trials."""
        expiry = timezone.now() - timedelta(days=1)
        user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=expiry,
        )
        assert user.has_demo_permission is False

    def test_has_demo_permission_other_tier(self):
        """Test that has_demo_permission is False for other active tiers."""
        user = AccountFactory(subscription=Subscription.BUSINESS_MANAGEMENT)
        assert user.has_demo_permission is False

    def test_has_demo_permission_no_expiry(self):
        """Test that has_demo_permission handles None expiry dates gracefully."""
        user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=None,
        )
        # Without an expiry date, it defaults to False or unexpired based on business logic, 
        # but safely evaluates to not expired (False) since not self.is_subscription_expired is True.
        assert user.has_demo_permission is True
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py -v`
Expected: FAIL due to AttributeError (property `has_demo_permission` does not exist on `Account`).

**Step 3: Write minimal implementation**
Modify `app/Account/models.py` to add `has_demo_permission` and refactor `has_subscription_tier` and `has_project_role`:
```python
    @property
    def has_demo_permission(self) -> bool:
        """Check if the user has an active, unexpired Demo subscription."""
        from app.Account.subscription_config import Subscription
        return self.subscription == Subscription.DEMO_TIER and not self.is_subscription_expired
```

And update `has_subscription_tier` (approx line 240) to check expiration for demo tier:
```python
        if self.subscription == Subscription.DEMO_TIER:
            return not self.is_subscription_expired
```

And update `has_project_role` (approx line 210):
```python
        if self.is_superuser or self.has_demo_permission:
            return True
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Account/models.py app/Account/tests/test_demo_tier.py
git commit -m "feat: implement Account.has_demo_permission dynamic property and verify"
```

---

### Task 2: Permission Mixins Standardization & Consultant Views Verification

**Files:**
- Modify: `app/core/Utilities/permissions.py`
- Modify: `app/Consultant/views/mixins.py`
- Test: `app/Consultant/tests/test_demo_tier_consultant.py`

**Step 1: Write the failing tests**
Add expired trial test cases in `app/Consultant/tests/test_demo_tier_consultant.py`:
```python
    def test_expired_demo_user_fails_group_permission_mixin(self):
        """Test that expired DEMO_TIER users fail group permission checks."""
        mixin = UserHasGroupGenericMixin()
        mixin.permissions = ["consultant"]
        
        # Set expired trial
        self.demo_user.subscription_expires_at = timezone.now() - timedelta(days=1)
        self.demo_user.save()

        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request

        self.assertFalse(mixin.test_func())

    def test_consultant_mixin_filters_clients_for_expired_demo_user(self):
        """Test that ConsultantMixin.get_clients filters clients for expired DEMO_TIER users."""
        mixin = ConsultantMixin()
        self.demo_user.subscription_expires_at = timezone.now() - timedelta(days=1)
        self.demo_user.save()

        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request

        clients = mixin.get_clients()
        self.assertEqual(clients.count(), 0)

    def test_payment_cert_mixin_raises_404_for_expired_demo_user(self):
        """Test that PaymentCertMixin blocks expired DEMO_TIER users."""
        from django.http import Http404
        mixin = PaymentCertMixin()
        self.demo_user.subscription_expires_at = timezone.now() - timedelta(days=1)
        self.demo_user.save()

        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request
        mixin.kwargs = {"project_pk": self.project.pk}

        with self.assertRaises(Http404):
            mixin.get_project()
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_demo_tier_consultant.py -v`
Expected: FAIL (expired demo users still pass because python checks are still hardcoded directly to the `DEMO_TIER` string and bypass expiration dates).

**Step 3: Write minimal implementation**
1. Modify `app/core/Utilities/permissions.py`:
Replace line 19-23 inside `UserHasGroupGenericMixin.test_func`:
```python
        # Allow access on Demo tier if subscription is active and not expired
        if getattr(
            self.request.user, "has_demo_permission", False
        ):
            return True
```

2. Modify `app/Consultant/views/mixins.py`:
* In `ConsultantMixin.get_clients` (line 24-28):
```python
            # Allow active DEMO_TIER users to see all CLIENT companies
            if getattr(
                self.request.user, "has_demo_permission", False
            ):
                pass
```
* In `PaymentCertMixin.get_project` (line 100-103):
```python
        # Allow active DEMO_TIER users to bypass consultant check
        if getattr(user, "has_demo_permission", False):
            return self.project
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_demo_tier_consultant.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add app/core/Utilities/permissions.py app/Consultant/views/mixins.py app/Consultant/tests/test_demo_tier_consultant.py
git commit -m "refactor: use Account.has_demo_permission in all base and views permission mixins"
```

---

### Task 3: Template Tags Cleanups

**Files:**
- Modify: `app/core/templatetags/template_extras.py`
- Test: `app/Account/tests/test_demo_tier.py`

**Step 1: Write the failing tests**
Add a test in `app/Account/tests/test_demo_tier.py` verifying the `project_roles` template filter with an expired demo user:
```python
    def test_demo_tier_project_roles_filter_expired(self):
        """Test that the projectroles filter does NOT bypass role checks for expired trials."""
        from app.core.templatetags.template_extras import project_roles
        from app.Project.tests.factories import ProjectFactory

        expiry = timezone.now() - timedelta(days=1)
        user = AccountFactory(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at=expiry,
        )
        project = ProjectFactory()

        roles = project_roles(user, project)
        # Should not return all roles; since user is not assigned to the project, should be empty/filtered
        assert roles.exists() is False
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py::TestDemoTier::test_demo_tier_project_roles_filter_expired -v`
Expected: FAIL (returns all roles instead of empty).

**Step 3: Write minimal implementation**
Modify `app/core/templatetags/template_extras.py` around line 60-63:
```python
    if user.is_superuser or getattr(user, "has_demo_permission", False):
        from app.Project.models import ProjectRole
        return ProjectRole.objects.all()
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_tier.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add app/core/templatetags/template_extras.py app/Account/tests/test_demo_tier.py
git commit -m "refactor: standardize template_extras filters to check has_demo_permission"
```

---

### Task 4: UI Navigation & Page Settings Adjustments

**Files:**
- Modify: `app/templates/nav.html`
- Modify: `app/Project/templates/project/project_setup.html`

**Step 1: Write the failing test / target validation**
Since HTML modifications are validated visually/manually, we target replacing direct subscription string checks:
1. `nav.html`:
   - Line 67 and Line 83 currently check `user.subscription == 'DEMO_TIER'`.
2. `project_setup.html`:
   - Checks `user.subscription == "DEMO_TIER"`.

**Step 2: Perform the replacement**
1. Modify `app/templates/nav.html`:
   - Change `user.subscription == 'DEMO_TIER'` to `user.has_demo_permission` on lines 67 and 83.
2. Modify `app/Project/templates/project/project_setup.html`:
   - Change `user.subscription == 'DEMO_TIER'` and `user.subscription != 'DEMO_TIER'` to `user.has_demo_permission` / `not user.has_demo_permission` where relevant.

**Step 3: Run full verification suite**
Run:
```bash
.venv\Scripts\python.exe -m pytest
```
Expected: PASS (All tests in the system pass)

**Step 4: Commit**
```bash
git add app/templates/nav.html app/Project/templates/project/project_setup.html
git commit -m "frontend: update navigation and project setup template checks to use has_demo_permission"
```
