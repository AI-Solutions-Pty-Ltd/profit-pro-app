# Space Thousands Separator Integration Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Modify the payment certificate PDF templates to format all currency/amount values with a space thousands separator and a dot decimal separator (e.g., `74 593.31`).

**Architecture:** Create a new Django template filter `space_intcomma` in `app/core/templatetags/template_extras.py` and apply it across the PDF templates.

**Tech Stack:** Python 3.13+, Django 5.2+, Pytest

---

### Task 1: Create tests for `space_intcomma` filter

**Files:**
* Create: `app/core/tests/test_template_extras.py`

**Step 1: Write the failing test**
Create `app/core/tests/test_template_extras.py` with:
```python
import pytest
from decimal import Decimal
from app.core.templatetags.template_extras import space_intcomma

def test_space_intcomma_with_floats():
    assert space_intcomma(12345.67) == "12 345.67"
    assert space_intcomma(74593.31) == "74 593.31"
    assert space_intcomma(0.0) == "0.00" or space_intcomma(0.0) == "0.0"

def test_space_intcomma_with_decimals():
    assert space_intcomma(Decimal("12345.67")) == "12 345.67"
    assert space_intcomma(Decimal("11189.00")) == "11 189.00"

def test_space_intcomma_with_strings():
    assert space_intcomma("12345.67") == "12 345.67"
    assert space_intcomma("12345") == "12 345"
    assert space_intcomma("-") == "-"
    assert space_intcomma(None) is None
    assert space_intcomma("") == ""
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/core/tests/test_template_extras.py`
Expected: Fail/ImportError because `space_intcomma` is not defined in `template_extras.py`.

**Step 3: Commit**
```bash
git add app/core/tests/test_template_extras.py
git commit -m "test: add tests for space_intcomma filter"
```

---

### Task 2: Implement `space_intcomma` in `app/core/templatetags/template_extras.py`

**Files:**
* Modify: `app/core/templatetags/template_extras.py`

**Step 1: Write minimal implementation**
Append the following implementation to the end of `app/core/templatetags/template_extras.py`:
```python
@register.filter(name="space_intcomma")
def space_intcomma(value):
    """Format a number with space thousands separator and dot decimal separator."""
    if value is None or value == "":
        return value
    try:
        val_str = str(value)
        if "." in val_str:
            parts = val_str.split(".")
            integer_part = f"{int(parts[0]):,}".replace(",", " ")
            return f"{integer_part}.{parts[1]}"
        else:
            return f"{int(val_str):,}".replace(",", " ")
    except (ValueError, TypeError):
        try:
            val = float(value)
            return f"{val:,.2f}".replace(",", " ")
        except (ValueError, TypeError):
            return value
```

**Step 2: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/core/tests/test_template_extras.py`
Expected: PASS

**Step 3: Commit**
```bash
git add app/core/templatetags/template_extras.py
git commit -m "feat: implement space_intcomma template filter"
```

---

### Task 3: Apply `space_intcomma` to Valterra RPM PDF front page

**Files:**
* Modify: `app/BillOfQuantities/templates/pdf_templates/valterra_rpm/1-front-page.html`

**Step 1: Apply filter in the template**
Modify the file `app/BillOfQuantities/templates/pdf_templates/valterra_rpm/1-front-page.html` to add `|space_intcomma`:
* Line 280: `R {{ project.total_contract_value|mul:0.2|floatformat:2|space_intcomma }}`
* Line 298: `{{ project.original_contract_value|floatformat:2|space_intcomma }}`
* Line 304: `{{ project.addendum_contract_value|floatformat:2|space_intcomma }}`
* Line 312: `{{ project.total_contract_value|floatformat:2|space_intcomma }}`
* Line 316: `{{ project.total_contract_value|mul:0.15|floatformat:2|space_intcomma }}`
* Line 320: `{{ project.total_contract_value|mul:1.15|floatformat:2|space_intcomma }}`
* Line 340: `{{ payment_certificate.progressive_to_date|floatformat:2|space_intcomma }}`
* Line 352: `{{ payment_certificate.progressive_to_date|floatformat:2|space_intcomma }}`
* Line 360: `{{ payment_certificate.progressive_to_date|floatformat:2|space_intcomma }}`
* Line 364: `{{ payment_certificate.progressive_previous|floatformat:2|space_intcomma }}`
* Line 368: `{{ payment_certificate.current_claim_total|floatformat:2|space_intcomma }}`
* Line 372: `{{ payment_certificate.current_claim_total|mul:0.15|floatformat:2|space_intcomma }}`
* Line 376: `{{ payment_certificate.current_claim_total|mul:1.15|floatformat:2|space_intcomma }}`
* Line 382: `Note: 5% Retention not deducted &mdash; handled by Valterra GSS. Retention: R {{ payment_certificate.current_claim_total|mul:0.05|floatformat:2|space_intcomma }}`

**Step 2: Run exporter tests to verify**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py`
Expected: PASS

**Step 3: Commit**
```bash
git add app/BillOfQuantities/templates/pdf_templates/valterra_rpm/1-front-page.html
git commit -m "style: apply space_intcomma to Valterra RPM front page template"
```

---

### Task 4: Apply `space_intcomma` to Valterra RPM PDF summary and detailed pages

**Files:**
* Modify: `app/BillOfQuantities/templates/pdf_templates/valterra_rpm/2-summary.html`
* Modify: `app/BillOfQuantities/templates/pdf_templates/valterra_rpm/3-detailed.html`

**Step 1: Replace `intcomma` with `space_intcomma`**
* In `2-summary.html`, replace all instances of `|intcomma` with `|space_intcomma`.
* In `3-detailed.html`, replace all instances of `|intcomma` with `|space_intcomma`.

**Step 2: Run exporter tests to verify**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py`
Expected: PASS

**Step 3: Commit**
```bash
git add app/BillOfQuantities/templates/pdf_templates/valterra_rpm/2-summary.html app/BillOfQuantities/templates/pdf_templates/valterra_rpm/3-detailed.html
git commit -m "style: apply space_intcomma to Valterra RPM summary and detailed templates"
```

---

### Task 5: Apply `space_intcomma` to Standard PDF layout pages

**Files:**
* Modify: `app/BillOfQuantities/templates/pdf_templates/1-front-page.html`
* Modify: `app/BillOfQuantities/templates/pdf_templates/line_items_table.html`

**Step 1: Replace `intcomma` with `space_intcomma`**
* In `1-front-page.html`, replace all instances of `|intcomma` with `|space_intcomma`.
* In `line_items_table.html`, replace all instances of `|intcomma` with `|space_intcomma`.

**Step 2: Run exporter tests to verify**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py`
Expected: PASS

**Step 3: Commit**
```bash
git add app/BillOfQuantities/templates/pdf_templates/1-front-page.html app/BillOfQuantities/templates/pdf_templates/line_items_table.html
git commit -m "style: apply space_intcomma to Standard PDF templates"
```
