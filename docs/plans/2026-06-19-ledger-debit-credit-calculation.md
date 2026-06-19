# Ledger Debit & Credit Calculations Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Correct the ledger calculations inside `PaymentCertificate` by subtracting credit amounts from debit amounts for all ledger models.

**Architecture:** Split the querysets inside `PaymentCertificate` methods using `.filter(transaction_type=...)` and subtract credit sums from debit sums using the existing `sum_queryset` utility.

**Tech Stack:** Django, Python, pytest

---

### Task 1: Clean up temporary edit in get_ledger_summary_items

**Files:**
- Modify: `app/BillOfQuantities/models/payment_certificate_models.py:475-495`
- Test: `app/BillOfQuantities/tests/test_payment_certificate_models.py`

**Step 1: Write the failing test**
None needed, as this is clean-up of a broken temporary line that is not tested yet.

**Step 2: Run test to verify it fails**
None.

**Step 3: Write minimal implementation**
Remove lines 480-483 in `app/BillOfQuantities/models/payment_certificate_models.py` that override `ap_current`.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_models.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add app/BillOfQuantities/models/payment_certificate_models.py
git commit -m "refactor: clean up temporary override in get_ledger_summary_items"
```

---

### Task 2: Update Current Certificate Ledger Helper Methods

**Files:**
- Modify: `app/BillOfQuantities/models/payment_certificate_models.py:551-605`
- Test: `app/BillOfQuantities/tests/test_payment_certificate_models.py`

**Step 1: Write the failing test**
In `app/BillOfQuantities/tests/test_payment_certificate_models.py`, add `test_current_ledger_totals_with_debits_and_credits`:
```python
    def test_current_ledger_totals_with_debits_and_credits(self):
        """Test that get_<type>_total methods subtract credit transactions from debit transactions."""
        from app.BillOfQuantities.tests.factories import (
            AdvancePaymentFactory,
            RetentionFactory,
            MaterialsOnSiteFactory,
            EscalationFactory,
            SpecialItemTransactionFactory,
        )
        from app.BillOfQuantities.models import BaseLedgerItem

        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)

        # 1. Advance Payments (Debit: 10000, Credit: 3000) -> Net: 7000
        AdvancePaymentFactory.create(
            project=project, payment_certificate=cert,
            transaction_type=BaseLedgerItem.TransactionType.DEBIT, amount=Decimal("10000.00")
        )
        AdvancePaymentFactory.create(
            project=project, payment_certificate=cert,
            transaction_type=BaseLedgerItem.TransactionType.CREDIT, amount=Decimal("3000.00")
        )

        # 2. Retention (Debit: 5000, Credit: 1000) -> Net: 4000
        RetentionFactory.create(
            project=project, payment_certificate=cert,
            transaction_type=BaseLedgerItem.TransactionType.DEBIT, amount=Decimal("5000.00")
        )
        RetentionFactory.create(
            project=project, payment_certificate=cert,
            transaction_type=BaseLedgerItem.TransactionType.CREDIT, amount=Decimal("1000.00")
        )

        assert cert.get_advance_payment_total() == Decimal("7000.00")
        assert cert.get_retention_total() == Decimal("4000.00")
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_models.py -k test_current_ledger_totals_with_debits_and_credits -v`
Expected: FAIL (returns sum of absolute values e.g. 13000 and 6000)

**Step 3: Write minimal implementation**
Modify `get_advance_payment_total`, `get_retention_total`, `get_materials_on_site_total`, `get_escalation_total`, `get_special_item_total`, and `get_special_item_totals_by_type` in `app/BillOfQuantities/models/payment_certificate_models.py` to filter by debit and credit types and subtract credits from debits.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_models.py -k test_current_ledger_totals_with_debits_and_credits -v`
Expected: PASS

**Step 5: Commit**
```bash
git add app/BillOfQuantities/models/payment_certificate_models.py app/BillOfQuantities/tests/test_payment_certificate_models.py
git commit -m "feat: correct current certificate ledger helper calculations to support debit and credit transactions"
```

---

### Task 3: Update Previous Certificates Ledger Properties

**Files:**
- Modify: `app/BillOfQuantities/models/payment_certificate_models.py:607-679`
- Test: `app/BillOfQuantities/tests/test_payment_certificate_models.py`

**Step 1: Write the failing test**
In `app/BillOfQuantities/tests/test_payment_certificate_models.py`, add `test_previous_ledger_totals_with_debits_and_credits`:
```python
    def test_previous_ledger_totals_with_debits_and_credits(self):
        """Test that previous_<type>_total properties subtract credit transactions from debit transactions from previous approved certificates."""
        from app.BillOfQuantities.tests.factories import (
            AdvancePaymentFactory,
            RetentionFactory,
        )
        from app.BillOfQuantities.models import BaseLedgerItem

        project = ProjectFactory.create()
        # Certificate 1 - Approved
        cert1 = PaymentCertificateFactory.create(project=project, certificate_number=1, status=PaymentCertificate.Status.APPROVED)
        # Certificate 2 - Draft
        cert2 = PaymentCertificateFactory.create(project=project, certificate_number=2, status=PaymentCertificate.Status.DRAFT)

        # C1 has Advance Payments (Debit: 20000, Credit: 5000) -> Net: 15000
        AdvancePaymentFactory.create(
            project=project, payment_certificate=cert1,
            transaction_type=BaseLedgerItem.TransactionType.DEBIT, amount=Decimal("20000.00")
        )
        AdvancePaymentFactory.create(
            project=project, payment_certificate=cert1,
            transaction_type=BaseLedgerItem.TransactionType.CREDIT, amount=Decimal("5000.00")
        )

        assert cert2.previous_advance_payment_total == Decimal("15000.00")
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_models.py -k test_previous_ledger_totals_with_debits_and_credits -v`
Expected: FAIL (returns sum of absolute values e.g. 25000)

**Step 3: Write minimal implementation**
Modify `previous_advance_payment_total`, `previous_retention_total`, `previous_materials_on_site_total`, `previous_escalation_total`, `previous_special_item_total`, and `previous_special_item_totals_by_type` in `app/BillOfQuantities/models/payment_certificate_models.py` to filter by debit and credit types and subtract credits from debits.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_models.py -k test_previous_ledger_totals_with_debits_and_credits -v`
Expected: PASS

**Step 5: Commit**
```bash
git add app/BillOfQuantities/models/payment_certificate_models.py app/BillOfQuantities/tests/test_payment_certificate_models.py
git commit -m "feat: correct previous certificate ledger properties calculations to support debit and credit transactions"
```
