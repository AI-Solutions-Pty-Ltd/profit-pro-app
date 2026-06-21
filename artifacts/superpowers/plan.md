# Implementation Plan: Negative Sign on Less Items

## Goal
Add a negative sign to the formatted number/currency values for cover page report items whose labels contain the word "less" (case-insensitive). This must display correctly in:
1. Browser HTML Cover Page view (`cover_page.html`).
2. Compiled PDF Cover Page report (`1-front-page.html`).
3. Exported Excel cover page spreadsheet (`cover_page_exporter.py`).
4. Live Cover Page configuration preview mockup (`cover_config.html`).

## Assumptions
- Only presentation-layer logic is modified. No database updates or total calculation changes are done.
- Labels are scanned case-insensitively for the substring `"less"`.
- If a value is already negative (e.g., a special item with negative value), it remains negative and is not double-negated.

## Plan

### Step 1: Update `get_resolved_cover_page_sections` in `payment_certificate_views.py`
- **Files**: [payment_certificate_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/payment_certificate_views.py)
- **Change**:
  - In `get_resolved_cover_page_sections`, check if the resolved label contains `"less"` (case-insensitive) and the raw numeric value is positive (`> 0`). If so, negate `raw_val` (make it negative).
  - Add a `"formatted_value"` key to the dictionary. Format it using South African Rand layout: if value is negative, format it as `-R X,XXX.XX` (prefixing `-R`), otherwise `R X,XXX.XX`.
- **Verify**: Run Django system check: `.venv\Scripts\python.exe manage.py check`

### Step 2: Update browser HTML template `cover_page.html`
- **Files**: [cover_page.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/payment_certificate/section_views/cover_page.html)
- **Change**:
  - In the loop rendering `field.style.is_mono` items, output `{{ field.formatted_value }}` instead of `R {{ field.raw_value|floatformat:2|intcomma }}`.
- **Verify**: Run pytest on payment certificate section views.

### Step 3: Update Excel exporter `cover_page_exporter.py`
- **Files**: [cover_page_exporter.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/exporters/cover_page_exporter.py)
- **Change**:
  - In `export_cover_page_to_xlsx`, scan `contract_rows` and `payment_rows` during iteration. If description contains `"less"` (case-insensitive) and value is positive, negate it.
- **Verify**: Run pytest on exporters.

### Step 4: Update JS Live Preview in `cover_config.html`
- **Files**: [cover_config.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/cover_config.html)
- **Change**:
  - In JS `renderSectionMock(tbody, secId)`, if a field label contains `"less"` (case-insensitive) and the mock value represents a positive currency (e.g. starts with `R` or has `0.00`), prefix it with a negative sign (e.g., `-R 900,000.00`).
- **Verify**: Verify the mock rendering is correct.

### Step 5: Add tests and verify
- **Files**:
  - [test_exporters.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_exporters.py)
  - [test_payment_certificate_section_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_payment_certificate_section_views.py)
- **Change**:
  - Add assertions verifying that the previous amount due (which has label starting with "LESS:") renders as negative (`-R 900,000.00` in HTML/mock, `-900,000.00` in Excel, and `-900 000.00` in PDF).
- **Verify**: Run all tests.

## Risks & mitigations
- **Double Negation**: Special items that are already negative in the database might be negated again.
  - *Mitigation*: Ensure the negation only triggers on positive values (`val > 0`).

## Rollback plan
- Git rollback: `git checkout -- <files>`
