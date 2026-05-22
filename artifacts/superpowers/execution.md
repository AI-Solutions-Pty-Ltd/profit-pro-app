# Demo Tier Expiration Lock-out - Execution Notes

## Step 1: Create the DemoExpiredMiddleware
* **Files changed**:
  * [NEW] [demo_expired_middleware.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/core/middleware/demo_expired_middleware.py)
* **What changed**:
  * Implemented `DemoExpiredMiddleware` which intercepts all incoming requests.
  * Verified that if a user is authenticated, has a `DEMO_TIER` subscription, and has expired, they are redirected to `users:account:demo-expired`.
  * Ignored administrative bypasses (superusers/staff), static files, media files, and browser reload paths.
  * Implemented AJAX/JSON safety returning a `403` JSON payload instead of an HTML redirect for API requests.
* **Verification command**: `.venv\Scripts\python.exe -m ruff check app/core/middleware/demo_expired_middleware.py`
* **Result**: PASS
