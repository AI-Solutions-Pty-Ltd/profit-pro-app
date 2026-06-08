# TDD Implementation Plan: SedgePro Webhook Invitation Refactor

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

### Goal
Refactor the SedgePro user invitation webhook (`SedgeProWebhookView`) to return the generated user setup URL (containing `uidb64` and `token` parameters) in the JSON response payload, and make the automated email notification conditional on a new boolean request parameter `"send_email"`.

### Assumptions
1. The webhook view is `SedgeProWebhookView` in `app/Account/views/auth_views.py`.
2. Existing tests are defined in `app/Account/tests/test_sedgepro_webhook.py`.
3. The custom onboarding/setup URL points to Django's standard reset/activation url pattern: `reset/<uidb64>/<token>/` which maps to `users:auth:password_reset_confirm`.
4. We must support both new users (who need a signup token & activation URL) and existing users (who already have an account setup, returning `signup_url: null`).
5. By default, `"send_email"` in the request payload is `False`. If omitted or `False`, no email is sent. If `True`, we send the email using Django's email backend.

### Plan

1. **Step 1: Update existing tests and add new tests in test_sedgepro_webhook.py (TDD First)**
   - **Files**: `app/Account/tests/test_sedgepro_webhook.py`
   - **Change**:
     - Update `test_webhook_success_new_user` and `test_webhook_success_existing_user_not_linked` to pass `"send_email": True` in the post payload, keeping their email assertion logic valid. Also assert that the response JSON contains `"signup_url"`.
     - Add `test_webhook_success_new_user_no_email` where `"send_email"` is omitted (or `False`). Assert that:
       - Response status is 200 OK.
       - `"signup_url"` in the response JSON is a valid URL containing `/users/auth/reset/<uidb64>/<token>/`.
       - No emails are sent (`len(mail.outbox) == 0`).
     - Add `test_webhook_success_existing_user_not_linked_no_email` where `"send_email"` is `False`. Assert that:
       - Response status is 200 OK.
       - `"signup_url"` in the response JSON is `None`.
       - No emails are sent (`len(mail.outbox) == 0`).
     - Update all existing success test cases to expect `"signup_url"` (which can be a string or null) in the JSON response for consistency.
   - **Verify**: Run `.venv\Scripts\python.exe -m pytest app/Account/tests/test_sedgepro_webhook.py -v` (expected to fail on new assertions).

2. **Step 2: Implement conditional emailing and token return in SedgeProWebhookView**
   - **Files**: `app/Account/views/auth_views.py`
   - **Change**:
     - Extract `send_email` from the request JSON payload (check both the root and the `record` wrapper if present), coercing/defaulting it to `False`.
     - Refactor the token/uid generation out of the `settings.USE_EMAIL` block so that we always generate `token`, `uid`, and the absolute `signup_url` for new users regardless of whether the email is sent.
     - Restructure the email sending block to only execute when `settings.USE_EMAIL` is `True` AND `send_email` is `True`.
     - Update successful JSON responses to return the `"signup_url"` parameter:
       - For newly invited users: the generated absolute signup URL.
       - For existing users or already linked users: `None`.
   - **Verify**: Run `.venv\Scripts\python.exe -m pytest app/Account/tests/test_sedgepro_webhook.py -v` (expected to PASS).

3. **Step 3: Run full verification**
   - **Files**: None
   - **Change**: Run ruff check and all pytest tests across the workspace.
   - **Verify**:
     - `.venv\Scripts\python.exe -m ruff check .`
     - `.venv\Scripts\python.exe -m pytest`

### Risks & mitigations
- **Risk**: Returning signup token in API response payload increases attack surface.
  - *Mitigation*: The endpoint is secured by custom `X-SedgePro-API-Key` headers and only sent over HTTPS/SSL. The token only works once and is valid for a short lifespan (24 hours).
- **Risk**: Retroactive changes breaking other parts of the system.
  - *Mitigation*: Full test suite execution verifies that no regressions are introduced.

### Rollback plan
- Revert changes using `git checkout` for `app/Account/views/auth_views.py` and `app/Account/tests/test_sedgepro_webhook.py`.
