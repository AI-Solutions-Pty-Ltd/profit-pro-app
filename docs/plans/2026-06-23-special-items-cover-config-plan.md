# Special Items Cover Config & Reports Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Integrate the custom ledger fields (`advance_payment`, `retention`, `material_on_site`, `other_specify`) into the default cover configuration, the view resolver, the PDF generator, and the Excel exporter.

**Architecture:** Update model default configuration dictionary, extend resolved sections calculations to dynamically fetch and compute current/previous ledger values, and update Excel/PDF exporter templates to support them.

**Tech Stack:** Python 3.13+, Django, openpyxl, PyPDF.

---

### Task 1: Update Default Cover Configuration in Project Model

**Files:**
- Modify: `app/Project/projects/projects_models.py`
- Test: `app/Project/tests/test_views.py`

**Step 1: Write the failing test**
In `app/Project/tests/test_views.py`, write a new test `test_default_cover_config_has_custom_ledger_fields` checking that the default config returned by `get_cover_page_config()` contains the four custom ledger fields.

```python
    def test_default_cover_config_has_custom_ledger_fields(self):
        """Test default cover page config contains custom ledger fields."""
        resolved = self.project.get_cover_page_config()
        fields = resolved["sections"]["section_c"]["fields"]
        field_ids = [f["id"] for f in fields]
        assert "advance_payment" in field_ids
        assert "retention" in field_ids
        assert "material_on_site" in field_ids
        assert "other_specify" in field_ids
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -k test_default_cover_config_has_custom_ledger_fields`
Expected: FAIL

**Step 3: Write minimal implementation**
In `app/Project/projects/projects_models.py` (around line 460), modify `default_config` for `section_c` to insert:
```python
                        {
                            "id": "advance_payment",
                            "label": "Advance payment",
                            "enabled": True,
                        },
                        {
                            "id": "retention",
                            "label": "Retention",
                            "enabled": True,
                        },
                        {
                            "id": "material_on_site",
                            "label": "Material on Site",
                            "enabled": True,
                        },
                        {
                            "id": "other_specify",
                            "label": "Other - Specify",
                            "enabled": True,
                        },
```
Keep `special_items` (for BoQ special items) as well.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -k test_default_cover_config_has_custom_ledger_fields`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Project/projects/projects_models.py app/Project/tests/test_views.py
git commit -m "feat: add custom ledger fields to default cover config"
```

---

### Task 2: Implement Custom Ledger Fields in View Resolver

**Files:**
- Modify: `app/BillOfQuantities/views/payment_certificate_views.py`
- Test: `app/BillOfQuantities/tests/test_payment_certificate_section_views.py`

**Step 1: Write the failing test**
In `app/BillOfQuantities/tests/test_payment_certificate_section_views.py`, write a new test class `TestCoverPageLedgerResolving` with a test to check that the custom ledger fields are correctly resolved.

```python
class TestCoverPageLedgerResolving:
    """Test resolving custom ledger fields for the cover page."""

    @pytest.mark.django_db
    def test_ledger_fields_resolved(self):
        """Verify custom ledger values are correctly calculated in resolved sections."""
        from decimal import Decimal
        from app.BillOfQuantities.tests.factories import (
            AdvancePaymentFactory,
            RetentionFactory,
            MaterialsOnSiteFactory,
            SpecialItemTransactionFactory,
            PaymentCertificateFactory,
        )
        from app.BillOfQuantities.views.payment_certificate_views import (
            get_resolved_cover_page_sections,
        )

        user, project, cert = _make_user_with_cert()

        # Create transactions for current and previous certificate
        prev_cert = PaymentCertificateFactory.create(
            project=project, certificate_number=1, status="APPROVED"
        )
        cert.certificate_number = 2
        cert.save()

        # Advance Payment (Current: 1000.00 debit, Prev: 5000.00 debit)
        AdvancePaymentFactory.create(
            project=project,
            payment_certificate=cert,
            amount=Decimal("1000.00"),
            transaction_type="DEBIT",
        )
        AdvancePaymentFactory.create(
            project=project,
            payment_certificate=prev_cert,
            amount=Decimal("5000.00"),
            transaction_type="DEBIT",
        )

        # Retention (Current: 200.00 credit, Prev: 800.00 credit)
        RetentionFactory.create(
            project=project,
            payment_certificate=cert,
            amount=Decimal("200.00"),
            transaction_type="CREDIT",
        )
        RetentionFactory.create(
            project=project,
            payment_certificate=prev_cert,
            amount=Decimal("800.00"),
            transaction_type="CREDIT",
        )

        # Special Item Transaction (OTHER) (Current: 300.00 debit, Prev: 600.00 debit)
        SpecialItemTransactionFactory.create(
            project=project,
            payment_certificate=cert,
            amount=Decimal("300.00"),
            transaction_type="DEBIT",
            special_item_type="OTHER",
        )
        SpecialItemTransactionFactory.create(
            project=project,
            payment_certificate=prev_cert,
            amount=Decimal("600.00"),
            transaction_type="DEBIT",
            special_item_type="OTHER",
        )

        sections = get_resolved_cover_page_sections(cert)
        fields = {f["id"]: f for sec in sections for f in sec["fields"]}

        # Check raw values
        assert fields["advance_payment"]["raw_value"] == Decimal("6000.00")
        assert fields["retention"]["raw_value"] == Decimal("-1000.00")
        assert fields["other_specify"]["raw_value"] == Decimal("900.00")
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_section_views.py -k TestCoverPageLedgerResolving`
Expected: FAIL (assertion error or fields missing / raw_value None)

**Step 3: Write minimal implementation**
In `app/BillOfQuantities/views/payment_certificate_views.py` `get_resolved_cover_page_sections`:
- Calculate the values for ledger components:
  ```python
  ap_current = payment_certificate.get_advance_payment_total()
  ap_prev = payment_certificate.previous_advance_payment_total
  advance_payment = ap_current + ap_prev

  ret_current = payment_certificate.get_retention_total()
  ret_prev = payment_certificate.previous_retention_total
  retention = ret_current + ret_prev

  mat_current = payment_certificate.get_materials_on_site_total()
  mat_prev = payment_certificate.previous_materials_on_site_total
  material_on_site = mat_current + mat_prev

  # Sum only those SpecialItemTransaction entries specifically categorized as type OTHER
  totals_by_type = payment_certificate.get_special_item_totals_by_type()
  prev_totals_by_type = payment_certificate.previous_special_item_totals_by_type
  other_current = totals_by_type.get("OTHER", Decimal("0.00"))
  other_prev = prev_totals_by_type.get("OTHER", Decimal("0.00"))
  other_specify = other_current + other_prev
  ```
- Override `progressive_to_date` (Sub Total), `progressive_previous` (LESS: Previous Amount Due), and `current_claim_total` (NET AMOUNT NOW CERTIFIED):
  ```python
  progressive_to_date = (
      work_progressive_to_date
      + advance_payment
      + retention
      + material_on_site
      + other_specify
  )
  progressive_previous = (
      work_progressive_previous
      + ap_prev
      + ret_prev
      + mat_prev
      + other_prev
  )
  current_claim_total = progressive_to_date - progressive_previous
  vat_val_payment = (
      current_claim_total * Decimal("0.15") if project.vat else Decimal("0.00")
  )
  total_certified = current_claim_total + vat_val_payment
  ```
- Resolve fields `advance_payment`, `retention`, `material_on_site`, and `other_specify` in `get_resolved_cover_page_sections` under `section_c` by setting their `raw_val` correctly.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_section_views.py -k TestCoverPageLedgerResolving`
Expected: PASS

**Step 5: Commit**
```bash
git add app/BillOfQuantities/views/payment_certificate_views.py app/BillOfQuantities/tests/test_payment_certificate_section_views.py
git commit -m "feat: resolve custom ledger fields and adjust cover page summary math"
```

---

### Task 3: Implement Custom Ledger Fields in Excel Exporter

**Files:**
- Modify: `app/BillOfQuantities/exporters/cover_page_exporter.py`
- Test: `app/BillOfQuantities/tests/test_exporters.py`

**Step 1: Write the failing test**
In `app/BillOfQuantities/tests/test_exporters.py`, write a new test `test_cover_page_export_custom_ledger_fields` checking that Excel output contains these cells and correctly calculates them.

```python
    def test_cover_page_export_custom_ledger_fields(self):
        """Test that exported Excel cover page contains the custom ledger fields and values."""
        from decimal import Decimal
        from app.BillOfQuantities.tests.factories import (
            AdvancePaymentFactory,
            RetentionFactory,
            PaymentCertificateFactory,
        )
        from app.BillOfQuantities.exporters.cover_page_exporter import export_cover_page_to_xlsx

        project = self.project
        cert = PaymentCertificateFactory.create(project=project, certificate_number=2)

        # Advance Payment (Current: 1000, Prev: 2000)
        AdvancePaymentFactory.create(
            project=project,
            payment_certificate=cert,
            amount=Decimal("1000.00"),
            transaction_type="DEBIT"
        )
        # We also mock previous_advance_payment_total to return 2000.00
        # or we can create previous cert with advance payment
        prev_cert = PaymentCertificateFactory.create(
            project=project, certificate_number=1, status="APPROVED"
        )
        AdvancePaymentFactory.create(
            project=project,
            payment_certificate=prev_cert,
            amount=Decimal("2000.00"),
            transaction_type="DEBIT"
        )

        wb = export_cover_page_to_xlsx(cert)
        ws = wb["Cover Page"]

        # Check sheet cells for values
        found_ap_row = None
        for r in range(1, 45):
            val = ws.cell(row=r, column=1).value
            if val and "advance" in str(val).lower():
                found_ap_row = r
                break

        assert found_ap_row is not None
        # Raw value at column 7
        assert ws.cell(row=found_ap_row, column=7).value == Decimal("3000.00")
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_cover_page_export_custom_ledger_fields`
Expected: FAIL

**Step 3: Write minimal implementation**
In `app/BillOfQuantities/exporters/cover_page_exporter.py`:
- Calculate the values for ledger components and overwrite:
  - `progressive_to_date`
  - `progressive_previous`
  - `current_claim_total`
  - `vat_val_payment`
  - `total_certified`
- In `sec_c_fields` loop, resolve:
  - `advance_payment`
  - `retention`
  - `material_on_site`
  - `other_specify`
  Add them to `payment_rows` with their computed value and field ID.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_cover_page_export_custom_ledger_fields`
Expected: PASS

**Step 5: Commit**
```bash
git add app/BillOfQuantities/exporters/cover_page_exporter.py app/BillOfQuantities/tests/test_exporters.py
git commit -m "feat: export custom ledger fields to Excel cover page"
```
