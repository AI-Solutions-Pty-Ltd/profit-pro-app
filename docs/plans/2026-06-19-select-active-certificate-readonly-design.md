# Design: Pre-select and Make Payment Certificate Field Read-only/Disabled

## Goal
The goal is to pre-select the current active `PaymentCertificate` on ledger forms and make the input read-only (disabled) so that users cannot change it. This applies to creating new ledger transactions and editing existing ones.

## Proposed Design (Option 1)
Modify the forms so that:
1. When instantiating the form, we identify the active payment certificate via `project.active_payment_certificate`.
2. If creating a new ledger transaction (no `instance.pk` exists), we set `payment_certificate`'s initial value to the active certificate.
3. In all cases (both creation and update), if an active certificate exists, we set `disabled = True` on the `payment_certificate` form field. Django will automatically handle this securely, rendering it as a disabled `<select>` dropdown and retaining the value correctly.

## Proposed Changes

### Forms

#### [MODIFY] [ledger_forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/forms/ledger_forms.py)
In all 4 form classes (`AdvancedPaymentCreateUpdateForm`, `RetentionCreateUpdateCreateForm`, `MaterialsOnSiteCreateUpdateForm`, `EscalationCreateUpdateForm`), update `__init__` to:
- Pre-select `project.active_payment_certificate` as initial if `instance.pk` is not set.
- Disable the `payment_certificate` field.

### Views

#### [MODIFY] [ledger_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/ledger_views.py)
In `SpecialItemTransactionCreateView.CreateForm` and `SpecialItemTransactionUpdateView.UpdateForm`, update `__init__` similarly to:
- Pre-select `project.active_payment_certificate` as initial if `instance.pk` is not set.
- Disable the `payment_certificate` field.

### Models Cleanup

#### [MODIFY] [payment_certificate_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/models/payment_certificate_models.py)
Clean up ruff rule A001 violations by renaming variables named `credits` to `credit_txns` or `credit_transactions` to resolve built-in shadowing.

---

## Verification Plan

### Automated Tests
- Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_views.py`
- Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_new_models.py`
- Run: `.venv\Scripts\python.exe -m ruff check .` to verify no lint errors.

### Manual Verification
- Verify that when creating or editing a ledger item, the "Payment Certificate" field is preloaded with the current active certificate and cannot be changed.
