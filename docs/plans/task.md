| Task | Status | Description |
| :--- | :--- | :--- |
| **Step 1: Create the DemoExpiredMiddleware** | [x] | Middleware blocking access for expired trial users and allowing AJAX safety / assets. |
| **Step 2: Implement Locked View and URL Routing** | [x] | Add DemoExpiredView view in account_views.py and routing in account_urls.py. |
| **Step 3: Design the Premium Locked View Template** | [x] | Create demo_expired.html layout with elegant styling, CSS backdrop blur, marketing redirection button, and secure Logout POST. |
| **Step 4: Register the Middleware in Settings** | [x] | Add DemoExpiredMiddleware to MIDDLEWARE list in settings/base.py. |
| **Step 5: Write Comprehensive Pytest Unit Tests** | [x] | Create unit tests using factories to verify redirection, exclusion bypasses, and AJAX 403. |
| **Step 6: Verification & Complete Review** | [/] | Run all pytest suites, check code quality with ruff, and update graphify. |
