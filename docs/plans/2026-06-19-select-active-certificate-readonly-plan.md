# Select Active Certificate Readonly Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Pre-select the current active `PaymentCertificate` on all ledger forms and make the input read-only (disabled) so that users cannot change it.

**Architecture:** Utilize Django form field's built-in `disabled=True` attribute inside form `__init__` methods after checking `project.active_payment_certificate`. This ensures standard Crispy Forms styling, proper browser-level disabling, and secure backend validation.

**Tech Stack:** Python 3.13, Django 4.2+, Pytest

---

### Task 1: Clean up `credits` Variable Shadowing in `payment_certificate_models.py`

**Files:**
- Modify: [payment_certificate_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/models/payment_certificate_models.py)
- Test: [test_payment_certificate_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_payment_certificate_models.py)

**Step 1: Write minimal code modification to rename `credits` to `credits_txn`**
Rename the local variable `credits` to `credits_txn` in all methods in `payment_certificate_models.py` (lines 556, 569, 582, 593, 604, 621, 654, 671, 688, 703, 718, 739) to resolve ruff shadowing error A001.

**Step 2: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_models.py -v`
Expected: PASS

**Step 3: Run ruff check to verify error is resolved**
Run: `.venv\Scripts\python.exe -m ruff check app/BillOfQuantities/models/payment_certificate_models.py`
Expected: PASS with no errors

**Step 4: Commit**
```bash
git add app/BillOfQuantities/models/payment_certificate_models.py
git commit -m "style: fix variable shadowing ruff warning for credits in payment certificate models"
```

---

### Task 2: Implement Active Certificate Pre-Selection & Disabling in Forms

**Files:**
- Modify: [ledger_forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/forms/ledger_forms.py)
- Test: [test_payment_certificate_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_payment_certificate_views.py)

**Step 1: Write code changes to form `__init__` methods**
In `ledger_forms.py`, for form classes `AdvancedPaymentCreateUpdateForm`, `RetentionCreateUpdateCreateForm`, `MaterialsOnSiteCreateUpdateForm`, and `EscalationCreateUpdateForm`, update the `__init__` block checking `self.project` to set `initial` and `disabled = True` for the field `payment_certificate`.

```python
        # Filter payment certificates to current project
        if self.project:
            self.fields[
                "payment_certificate"
            ].queryset = self.project.payment_certificates.all().order_by(  # type: ignore
                "-created_at"
            )
            active_cert = self.project.active_payment_certificate
            if active_cert:
                if not self.instance.pk:
                    self.fields["payment_certificate"].initial = active_cert
                self.fields["payment_certificate"].disabled = True
```

**Step 2: Run tests to verify existing behaviors still pass**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_views.py -v`
Expected: PASS

**Step 3: Commit**
```bash
git add app/BillOfQuantities/forms/ledger_forms.py
git commit -m "feat: pre-select and disable payment_certificate field on ledger forms"
```

---

### Task 3: Implement Active Certificate Pre-Selection & Disabling in SpecialItemTransaction views

**Files:**
- Modify: [ledger_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/ledger_views.py)
- Test: [test_special_item_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_special_item_views.py)

**Step 1: Write code changes to inline form classes**
In `ledger_views.py`, for `SpecialItemTransactionCreateView.CreateForm` and `SpecialItemTransactionUpdateView.UpdateForm`, update the `__init__` methods to match the behavior:
```python
            # Filter payment certificates to current project
            if self.project:
                self.fields[
                    "payment_certificate"
                ].queryset = self.project.payment_certificates.all().order_by(  # type: ignore
                    "-created_at"
                )
                active_cert = self.project.active_payment_certificate
                if active_cert:
                    if not self.instance.pk:
                        self.fields["payment_certificate"].initial = active_cert
                    self.fields["payment_certificate"].disabled = True
```

**Step 2: Run tests to verify all tests pass**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_special_item_views.py -v`
Expected: PASS

**Step 3: Run full test suite and quality checks**
Run: `.venv\Scripts\python.exe -m pytest`
Run: `.venv\Scripts\python.exe -m ruff check .`
Expected: All checks PASS

**Step 4: Commit**
```bash
git add app/BillOfQuantities/views/ledger_views.py
git commit -m "feat: pre-select and disable payment_certificate field on special item ledger forms"
```
