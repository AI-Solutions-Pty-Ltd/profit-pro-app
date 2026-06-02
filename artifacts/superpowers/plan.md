# SedgePro Webhook Invitation Flow Implementation Plan

## Goal
Develop a secure API webhook endpoint in the Django backend of Profit Pro that allows **SedgePro** to trigger a user invitation after a successful payment. This endpoint will receive an email and a client reference, find/create the corresponding `Account` with an unusable password, link the user to the associated `Company` matching the client reference, and send a customized activation/onboarding email.

---

## User Review Required
We will configure SedgePro to authenticate using a shared API key passed via the custom HTTP header `X-SedgePro-API-Key`. This key should be kept securely in environment variables on your servers.

---

## Open Questions
No open questions at this stage. We have established that the client reference provided by SedgePro corresponds to the `registration_number` field of the `Company` model.

---

## Proposed Changes

### Goal
Implement secure integration via webhook.

### Assumptions
1. SedgePro will authenticate with Profit Pro using a shared API key passed via the HTTP header `X-SedgePro-API-Key`.
2. The shared API key is stored in Django settings as `settings.SEDGEPRO_API_KEY` (configured via environment variables).
3. The client reference provided by SedgePro corresponds to the `registration_number` field of the `Company` model.
4. Python 3.13 virtual environment is active in the workspace at `.venv`.

---

## Plan

### 1. Write Webhook Tests (TDD First)
* **Files**: [NEW] [test_sedgepro_webhook.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/test_sedgepro_webhook.py)
* **Change**:
  - Implement comprehensive integration tests validating SedgePro signature authentication (missing, invalid, valid).
  - Test successful user invitations for:
    - A completely new user (should create user with unusable password and send invitation email).
    - An existing user not currently linked to the client (should link user and send welcome notification email).
    - An existing user already linked to the client (idempotent path; returns success without duplicate actions).
  - Test validation errors (invalid client reference/company, malformed payload).
* **Verify**:
  - Run: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_sedgepro_webhook.py`
  - Expected: Fail with `NoReverseMatch` (since route is not registered).

### 2. Register Webhook URL Pattern
* **Files**: [MODIFY] [auth_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/urls/auth_urls.py)
* **Change**:
  - Add path `sedgepro/webhook/` routing to `auth_views.SedgeProWebhookView.as_view()`.
* **Verify**:
  - Run: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_sedgepro_webhook.py`
  - Expected: Fail with `ImportError: cannot import name 'SedgeProWebhookView'`.

### 3. Define SedgePro API Credentials in Settings
* **Files**: [MODIFY] [base.py](file:///c:/Users/nebst/Projects/profit-pro-app/settings/base.py)
* **Change**:
  - Define `SEDGEPRO_API_KEY = os.environ.get("SEDGEPRO_API_KEY", "test-sedgepro-key")`.
* **Verify**:
  - Check syntax: `.venv\Scripts\python.exe -m ruff check settings/base.py`

### 4. Implement SedgeProWebhookView
* **Files**: [MODIFY] [auth_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/views/auth_views.py)
* **Change**:
  - Define `SedgeProWebhookView` as a class-based view extending `View`.
  - Apply `method_decorator(csrf_exempt, name='dispatch')` to bypass CSRF token checks for server-to-server webhook requests.
  - Implement API key verification: validate `X-SedgePro-API-Key` matches `settings.SEDGEPRO_API_KEY`.
  - Validate and decode the JSON payload (required keys: `email` and `client_reference`).
  - Resolve the target `Company` matching `registration_number=client_reference` and `type=Company.Type.CLIENT`. Return 400 if not found.
  - In a `transaction.atomic()` database context:
    - Attempt to fetch existing `Account` by lowercase email.
    - If new: create user using `Account.objects.create_user(...)` with an unusable password.
    - Add user to `consultant` permission group.
    - Link user to target `Company` (`company.users.add(user)`).
    - Send activation token link or notification email based on whether user is new or existing.
* **Verify**:
  - Run: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_sedgepro_webhook.py -v`
  - Expected: PASS

### 5. Verify Entire Codebase Integrity
* **Files**: None
* **Change**: Run full test suites and code formatting tools to ensure everything is correct and has no lint issues.
* **Verify**:
  - Run: `.venv\Scripts\python.exe -m ruff check .`
  - Run: `.venv\Scripts\python.exe -m pytest`
  - Expected: Pass ruff check and all unit tests.

---

## Verification Plan

### Automated Tests
- Integration tests: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_sedgepro_webhook.py -v`
- Full test suite: `.venv\Scripts\python.exe -m pytest`

---

## Risks & Mitigations
* **Risk**: API key exposed in repository logs.
  - *Mitigation*: API key is parsed via standard environment variables and defaulted safely for local test validation.
* **Risk**: Duplicate webhook posts during network delay retries.
  - *Mitigation*: Webhook view is designed to be fully idempotent. If the user is already linked to the target client, it returns a 200 OK without sending duplicate activation emails.

---

## Rollback Plan
- Revert routing changes in [auth_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/urls/auth_urls.py).
- Revert custom view implementations in [auth_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/views/auth_views.py).
- Remove [test_sedgepro_webhook.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/test_sedgepro_webhook.py).
