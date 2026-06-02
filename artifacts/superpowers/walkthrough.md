# SedgePro Webhook Invitation Flow Walkthrough

We have successfully designed, built, and verified the secure, idempotent server-to-server webhook endpoint that integrates **SedgePro** payments with **Profit Pro** user invitations.

---

## Technical Accomplishments

### 1. Endpoint Routing
* **Endpoint Path**: `/users/auth/sedgepro/webhook/`
* **Route Name**: `users:auth:sedgepro_webhook`
* **File Modified**: [auth_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/urls/auth_urls.py)
* **View Mapping**: Configured the route to map directly to our new custom View class `auth_views.SedgeProWebhookView`.

### 2. View Implementation
* **Class**: `SedgeProWebhookView`
* **File Modified**: [auth_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/views/auth_views.py)
* **Logic Summary**:
  - **CSRF Bypass**: Applied `csrf_exempt` globally to allow secure, server-to-server headless POST requests.
  - **Header Authentication**: Securely authenticates incoming requests by validating the `X-SedgePro-API-Key` header against `settings.SEDGEPRO_API_KEY`.
  - **Payload Validation**: Decodes the JSON payload and validates required `email` and `client_reference` attributes.
  - **Client Resolution**: Queries the `Company` (Client) organization model using the incoming `client_reference` against the company's `registration_number`.
  - **Transactional Account Provisioning**: Within a `transaction.atomic()` database context, safely creates new `Account` records using `create_user` (giving them an unusable password and linking them to the `consultant` group) or resolves existing users.
  - **Client Affiliation**: Appends the resolved account directly to the client company's ManyToMany `users` collection.
  - **Idempotent Notification Dispatch**:
    - **For new users**: Dispatches a secure activation email using the `client/password_reset_email.html` template.
    - **For existing unlinked users**: Associates them with the client organization and dispatches a notification email via `client/client_added_email.html`.
    - **For existing linked users**: Instantly returns a `200 OK` success payload without executing duplicate actions or dispatching duplicate emails.

### 3. API Settings
* **File Modified**: [base.py](file:///c:/Users/nebst/Projects/profit-pro-app/settings/base.py)
* **Configuration**: Added the settings configuration variable `SEDGEPRO_API_KEY = os.getenv("SEDGEPRO_API_KEY", "test-sedgepro-key")` to safely ingest API tokens from system environment variables.

### 4. Integration Tests
* **File Created**: [test_sedgepro_webhook.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/test_sedgepro_webhook.py)
* **Test Suite Details**:
  - `test_webhook_unauthorized_missing_header`: Validates authentication blocks requests without headers.
  - `test_webhook_unauthorized_invalid_key`: Validates blocks on invalid API keys.
  - `test_webhook_invalid_json`: Handles malformed POST bodies.
  - `test_webhook_missing_required_fields`: Ensures validation checks for email and client reference.
  - `test_webhook_company_not_found`: Gracefully rejects invalid client codes.
  - `test_webhook_success_new_user`: Asserts new accounts are set up correctly, grouped, linked, and activation emails are sent.
  - `test_webhook_success_existing_user_not_linked`: Asserts existing accounts are linked and notification emails are sent.
  - `test_webhook_success_existing_user_already_linked`: Asserts idempotent execution prevents double emails.

---

## Verification Results

### 1. Webhook Unit Tests
All 8 integration tests pass with clean outputs:
```bash
.venv\Scripts\python.exe -m pytest app/Account/tests/test_sedgepro_webhook.py -v
```
**Results**:
```
app/Account/tests/test_sedgepro_webhook.py::TestSedgeProWebhookView::test_webhook_unauthorized_missing_header PASSED
app/Account/tests/test_sedgepro_webhook.py::TestSedgeProWebhookView::test_webhook_unauthorized_invalid_key PASSED
app/Account/tests/test_sedgepro_webhook.py::TestSedgeProWebhookView::test_webhook_invalid_json PASSED
app/Account/tests/test_sedgepro_webhook.py::TestSedgeProWebhookView::test_webhook_missing_required_fields PASSED
app/Account/tests/test_sedgepro_webhook.py::TestSedgeProWebhookView::test_webhook_company_not_found PASSED
app/Account/tests/test_sedgepro_webhook.py::TestSedgeProWebhookView::test_webhook_success_new_user PASSED
app/Account/tests/test_sedgepro_webhook.py::TestSedgeProWebhookView::test_webhook_success_existing_user_not_linked PASSED
app/Account/tests/test_sedgepro_webhook.py::TestSedgeProWebhookView::test_webhook_success_existing_user_already_linked PASSED

======================= 8 passed, 9 warnings in 49.07s ========================
```

### 2. Full Account Suite Checks
Executing the complete authentication and account model suite ensures no regressions were introduced to related structures:
```bash
.venv\Scripts\python.exe -m pytest app/Account/tests/
```
**Results**:
```
================= 87 passed, 39 warnings in 72.32s (0:01:12) ==================
```

### 3. Syntax Linter Validation
Running the ruff linter on all modified files returns zero errors:
```bash
.venv\Scripts\python.exe -m ruff check app/Account/urls/auth_urls.py app/Account/views/auth_views.py app/Account/tests/test_sedgepro_webhook.py
```
**Results**:
```
All checks passed!
```
