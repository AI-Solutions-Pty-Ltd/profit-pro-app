# Demo Tier Expiration Lock-out System - Implementation Plan

## Goal
To implement robust server-side middleware that lock-protects the Profit Pro application when a user's `DEMO_TIER` trial has expired. Expired users will be redirected to a visually stunning, non-dismissable locked view at `/users/account/demo-expired/` featuring a high-impact call to action to upgrade on the marketing website, alongside a functional logout mechanism.

## Assumptions
* The target environment is a Django 5.2 application running on Python 3.13+.
* The custom user model `Account` already exposes the properties `subscription == Subscription.DEMO_TIER` and `is_subscription_expired` which return boolean values for active trials vs. expired states.
* Superusers/staff should bypass the expiration checks to enable administrative support.
* Third-party/static assets and standard auth workflows (e.g. login, logout, password resets) should remain accessible.

---

## Plan

### Step 1: Create the DemoExpiredMiddleware
* **Files**:
  * [NEW] [demo_expired_middleware.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/core/middleware/demo_expired_middleware.py)
* **Change**:
  * Write a Django middleware checking if the logged-in user has an expired `DEMO_TIER` subscription.
  * If expired, block access to any URL NOT in a safe list (safe list includes: `/users/account/demo-expired/`, `/users/auth/logout/`, login/registration routes, django-browser-reload, admin routes for superusers, static, and media assets).
  * Safe-guard AJAX/JSON endpoints: if an AJAX request is intercepted, return a `403 Forbidden` JSON payload: `{"error": "Demo trial period has expired"}` instead of a redirect.
* **Verify**:
  * Run syntax validation: `.venv\Scripts\python.exe -m ruff check app/core/middleware/demo_expired_middleware.py`

### Step 2: Implement Locked View and URL Routing
* **Files**:
  * [MODIFY] [account_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/views/account_views.py)
  * [MODIFY] [account_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/urls/account_urls.py)
* **Change**:
  * Create `DemoExpiredView(LoginRequiredMixin, TemplateView)` in `account_views.py`. Add a check: if an active paid user or active trial user tries to access `/demo-expired/` manually, redirect them back to the `home` view.
  * Wire the URL pattern: `path("demo-expired/", account_views.DemoExpiredView.as_view(), name="demo-expired")` in `account_urls.py`.
* **Verify**:
  * Run syntax check: `.venv\Scripts\python.exe -m ruff check app/Account/`

### Step 3: Design the Premium Locked View Template
* **Files**:
  * [NEW] [demo_expired.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/templates/account/demo_expired.html)
* **Change**:
  * Create a stunning standalone layout (no header/footer navigation to prevent any UI leakage).
  * Design using Outfit/Inter typography, deep backdrop blur effects, a luxurious card structure, clear alerts, and visual micro-animations.
  * Embed a massive, vibrant gradient button leading to `https://sedgepro.co.za/#prelaunch-promotion`.
  * Display a secure, styled "Logout" button that POSTs to the logout view, ensuring the user can switch profiles safely.
* **Verify**:
  * Run template syntax check: `.venv\Scripts\python.exe manage.py check`

### Step 4: Register the Middleware in Settings
* **Files**:
  * [MODIFY] [base.py](file:///c:/Users/nebst/Projects/profit-pro-app/settings/base.py)
* **Change**:
  * Append `"app.core.middleware.demo_expired_middleware.DemoExpiredMiddleware"` to the `MIDDLEWARE` list in settings.
* **Verify**:
  * Run django configuration checks: `.venv\Scripts\python.exe manage.py check`

### Step 5: Write Comprehensive Pytest Unit Tests
* **Files**:
  * [NEW] [test_demo_lockout.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/test_demo_lockout.py)
* **Change**:
  * Import factories from `app/Account/tests/factories.py` (avoid manual creation).
  * Write assertions verifying:
    * Active demo user can access the app dashboard freely.
    * Expired demo user is blocked and redirected to the lockout page on all dashboards.
    * Expired demo user can still successfully access the logout URL.
    * Active paid users visiting `/demo-expired/` are redirected to the homepage.
    * AJAX calls from expired users return `403` JSON payloads.
* **Verify**:
  * Run the unit tests: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_lockout.py -v`

---

## Risks & mitigations
* **Risk**: Infinite Redirect Loop.
  * *Mitigation*: Carefully define safe paths in the middleware using Django's reverse resolution (`resolve(request.path).view_name`) to exclude the lockout view, login/logout, and password flows explicitly.
* **Risk**: Intercepting static/media assets, breaking styling.
  * *Mitigation*: Exclude any requests matching `settings.STATIC_URL` or `settings.MEDIA_URL` from the expiration interceptor logic.

## Rollback plan
* To rollback, simply remove `"app.core.middleware.demo_expired_middleware.DemoExpiredMiddleware"` from the `MIDDLEWARE` setting in `settings/base.py` and delete/revert the added files.

---

### PERSISTENCE NOTE
Now persisting this plan to `artifacts/superpowers/plan.md`.
