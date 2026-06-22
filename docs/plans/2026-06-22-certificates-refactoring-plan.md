# Certificates Refactoring Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Refactor and fix the Payment Certificates module (PDF, Excel, UI template, ledger cancel/success redirects, and download performance bypasses).

**Architecture:** 
1. Add natural sorting of bills to `tasks.py` and modify `get_valuation_summary_data()`.
2. Clear zeros/amounts for heading rows (`is_work=False`) in browser `tables/line_items.html` and Excel exporter `detailed_report_exporter.py`.
3. Add a page-break table for Contractual Special Items in the Valuation Summary PDF template `2-summary.html`.
4. Update `payment_certificate_views.py` download views to serve pre-generated files if default selections are made.
5. Apply back/cancel redirects to certificate edit page for all ledger views/modals and forms.
6. Remove bottom links from `payment_certificate_edit.html` empty states.

**Tech Stack:** Python 3.11, Django 5.2, openpyxl, pytest, ReportLab (xhtml2pdf)

---

### Task 1: Add natural sorting helper and update Valuation Summary data sorting

**Files:**
- Modify: [tasks.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tasks.py)

**Step 1: Write a unit test verifying natural sorting in get_valuation_summary_data**
Update `app/BillOfQuantities/tests/test_exporters.py` or write test in `app/BillOfQuantities/tests/test_payment_certificate_views.py`. Let's add natural sorting test in [test_exporters.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_exporters.py).

```python
def test_bill_natural_sorting():
    from app.BillOfQuantities.tasks import natural_key
    assert natural_key("Bill 2") < natural_key("Bill 10")
    assert natural_key("2") < natural_key("10")
```

**Step 2: Run test to verify it fails/passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_bill_natural_sorting -v`

**Step 3: Implement natural_key and sorting in tasks.py**
Add `natural_key` in `tasks.py`:
```python
import re

def natural_key(text):
    if not text:
        return [float('inf')]
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]
```
And inside `get_valuation_summary_data()`:
```python
        if bill_id not in struct["bills"]:
            struct["bills"][bill_id] = {
                "name": item.bill.name,
                "bill_number": item.bill.bill_number or "",
                "budget": Decimal("0.00"),
                ...
```
And change the sorted bills:
```python
        sorted_bills = sorted(
            s_data["bills"].values(),
            key=lambda b: (natural_key(b["bill_number"]), b["name"])
        )
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_bill_natural_sorting -v`

**Step 5: Commit**
Run: `git add app/BillOfQuantities/tasks.py app/BillOfQuantities/tests/test_exporters.py; git commit -m "feat: implement natural sorting of bills by bill number"`

---

### Task 2: Update Valuation Summary title and add Contractual Special Items in PDF template `2-summary.html`

**Files:**
- Modify: [2-summary.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/pdf_templates/valterra_rpm/2-summary.html)

**Step 1: Update title heading**
Replace `BILL OF QUANTITIES &mdash; SUMMARY` with `VALUATION SUMMARY` at line 149 of `2-summary.html`.

**Step 2: Append the Contractual Special Items section at the bottom of the template**
Copy the Contractual Special Items page-break block layout from `3-detailed.html` into `2-summary.html` before the closed body tag, styling it appropriately.

**Step 3: Verify PDF compilation manually or via a unit test**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_views.py -v`

**Step 4: Commit**
Run: `git add app/BillOfQuantities/templates/pdf_templates/valterra_rpm/2-summary.html; git commit -m "style: rename title and include contractual special items table in summary PDF"`

---

### Task 3: Excel Valuation Summary Export Cleanup

**Files:**
- Modify: [summary_report_exporter.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/exporters/summary_report_exporter.py)
- Modify: [payment_certificate_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/models/payment_certificate_models.py)

**Step 1: Retrieve display labels for special item types**
In `payment_certificate_models.py` inside `get_ledger_summary_items()` (around line 538):
```python
        for item_type, current in totals_by_type.items():
            prev = prev_totals_by_type.get(item_type, Decimal("0.00"))
            if current != 0 or prev != 0:
                from .ledger_models import SpecialItemTransaction
                label = dict(SpecialItemTransaction.SpecialItemType.choices).get(item_type, item_type)
                items.append(
                    {
                        "description": label,
                        "previous_amount": prev,
                        "current_amount": current,
                        "total_amount": prev + current,
                    }
                )
```

**Step 2: Excel cleanup in summary_report_exporter.py**
* Remove lines 305-308 (the "Ledger Totals" header row creation).
* Change `value="SUBTOTAL WORK DONE"` to `value="Total Work Done to Date"` at line 160.
* Remove lines 327-353 (the "Subtotal Ledger Items" row creation).

**Step 3: Run existing exporter tests**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -v`

**Step 4: Commit**
Run: `git add app/BillOfQuantities/exporters/summary_report_exporter.py app/BillOfQuantities/models/payment_certificate_models.py; git commit -m "refactor: cleanup Excel Valuation Summary headers, subtotals, and choices display labels"`

---

### Task 4: Zeros exclusion on Heading Rows (`is_work=False`) in Web UI and Excel Detailed Exporter

**Files:**
- Modify: [line_items.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/payment_certificate/tables/line_items.html)
- Modify: [detailed_report_exporter.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/exporters/detailed_report_exporter.py)

**Step 1: Colspan the description for headings in line_items.html**
In `tables/line_items.html`, inside the loop (line 30):
```django
                        {% for package_group in bill_group.packages %}
                            {% for line_item in package_group.line_items %}
                                {% if not line_item.is_work %}
                                    <tr class="bg-gray-50 font-bold hover:bg-gray-100">
                                        <td class="px-3 py-2 text-sm text-gray-950 whitespace-nowrap">{{ line_item.item_number|default:"" }}</td>
                                        <td class="px-3 py-2 text-sm text-gray-950" colspan="8">{{ line_item.description }}</td>
                                    </tr>
                                {% else %}
                                    <tr class="hover:bg-gray-50">
                                        ... normal work items columns ...
                                    </tr>
                                {% endif %}
```

**Step 2: Clear numeric columns in detailed_report_exporter.py**
In standard line items loop (lines 213-231):
```python
                    val_map = {
                        ...
                    }
                    if not item.is_work:
                        val_map.update({
                            "budgeted_quantity": None,
                            "unit_price": None,
                            "total_price": None,
                            "total_qty": None,
                            "total_claimed": None,
                            "previous_qty": None,
                            "previous_claimed": None,
                            "current_qty": None,
                            "current_claim": None,
                        })
```
And inside special/addendum loops (lines 459 and 525), if `item.is_work` is False, set numeric cell values to `None`.

**Step 3: Run exporter and view tests**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -v`

**Step 4: Commit**
Run: `git add app/BillOfQuantities/templates/payment_certificate/tables/line_items.html app/BillOfQuantities/exporters/detailed_report_exporter.py; git commit -m "style: remove zero amounts from heading items in Web UI and Excel"`

---

### Task 5: PDF/XLSX pre-generated serving bypass for default selections

**Files:**
- Modify: [payment_certificate_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/payment_certificate_views.py)

**Step 1: Implement selections bypass in PDF and XLSX download views**
For:
- `PaymentCertificateDownloadPDFView`
- `PaymentCertificateDownloadAbridgedPDFView`
- `PaymentCertificateDownloadUnifiedXLSXView`
- `PaymentCertificateDownloadUnifiedAbridgedXLSXView`

Add the check:
```python
        has_selections = any(k in request.GET for k in ["front", "summary", "detailed"])
        if has_selections:
            include_front = request.GET.get("front") in ["1", "on", "true"]
            include_summary = request.GET.get("summary") in ["1", "on", "true"]
            include_detailed = request.GET.get("detailed") in ["1", "on", "true"]
            force_regenerate = bool(request.GET.get("force"))
            
            if include_front and include_summary and include_detailed and not force_regenerate:
                has_selections = False
```

**Step 2: Run download tests**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_views.py -v`

**Step 3: Commit**
Run: `git add app/BillOfQuantities/views/payment_certificate_views.py; git commit -m "perf: serve pre-generated files directly if default options are selected"`

---

### Task 6: Context-aware cancel buttons and success redirects on ledger transactions

**Files:**
- Modify: [ledger_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/ledger_views.py)
- Create: [special_item_confirm_delete.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/special_item_confirm_delete.html)
- Modify: [special_item_confirm_delete_modal.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/modals/special_item_confirm_delete_modal.html)
- Modify: [special_item_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/special_item_views.py)
- Modify: forms templates (advance payment, retention, materials, escalation, special item forms and delete confirms) to respect `cancel_url`.

**Step 1: Correct `form.action` in `special_item_confirm_delete_modal.html`**
Change `form.action = \`/projects/\${projectPk}/special-items/\${txnId}/delete/\`;` to:
`form.action = \`/bill-of-quantities/project/\${projectPk}/special-items-ledger/\${txnId}/delete/\`;`

**Step 2: Add `cancel_url` and update `get_success_url` in ledger and special item views**
In `ledger_views.py` and `special_item_views.py`, intercept `payment_certificate_id` query param or check if `self.object.payment_certificate` is present.
If a certificate context exists:
- Cancel URL should reverse `"bill_of_quantities:payment-certificate-edit"`
- Success URL should redirect back to `"bill_of_quantities:payment-certificate-edit"`

**Step 3: Update templates to check `cancel_url`**
In `ledger/components/*_form_component.html` and `ledger/components/*_confirm_delete_component.html` (and also `special_item_form.html`):
Update the Cancel link `href` to:
`href="{% if cancel_url %}{{ cancel_url }}{% else %}{% url 'bill_of_quantities:...' project.pk %}{% endif %}"`

**Step 4: Run tests**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_views.py -v`

**Step 5: Commit**
Run: `git add app/BillOfQuantities/views/ app/BillOfQuantities/templates/; git commit -m "feat: support context-aware redirects back to payment-certificate-edit"`

---

### Task 7: Remove Add Addendum Item and Add Special Item links from Certificate Edit Page

**Files:**
- Modify: [payment_certificate_edit.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/payment_certificate/payment_certificate_edit.html)

**Step 1: Remove "Add Addendum Item" button link**
Delete lines 539-543 in `payment_certificate_edit.html`.

**Step 2: Remove "Add Special Item" button link**
Delete lines 603-607 in `payment_certificate_edit.html`.

**Step 3: Verify template compiles**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_views.py -v`

**Step 4: Commit**
Run: `git add app/BillOfQuantities/templates/payment_certificate/payment_certificate_edit.html; git commit -m "style: remove bottom add buttons from empty states in edit mode"`
