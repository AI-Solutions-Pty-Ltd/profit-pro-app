## Goal
Group Addendum Line Items, Special Items, and Ledger Totals Summary Items into a single table called "Contractual Special Items", with columns: Description, Previous Amount, Current Amount, and Total Amount, including subtotals for each section and a grand total. Integrate this table across all views (Valuation Summary, View Detailed, Detail pages), the PDF payment certificate, and the Excel Detailed and Summary exports.

## Assumptions
- Addendum Line Items are `LineItem` instances where `addendum=True` and `special_item=False`.
- Special Items are `LineItem` instances where `special_item=True` and `addendum=False`.
- Ledger Totals are the summary adjustments (Advance Payments, Retention, Materials on Site, Escalation, and Other special item types).
- Calculations of all subtotals and grand totals must match existing database/model fields exactly.

## Plan

### Step 1: Update PaymentCertificate Model Properties
- **Files**: [payment_certificate_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/models/payment_certificate_models.py)
- **Change**:
  - Add `addendum_budget_total` property.
  - Add properties: `contractual_special_items_progressive_previous`, `contractual_special_items_current_claim_total`, `contractual_special_items_progressive_to_date`, `has_contractual_special_items`.
  - Add `get_ledger_summary_items()` helper method.
  - Update `grand_total_progressive_previous` and `grand_total_progressive_to_date` to include special items (use `progressive_previous`/`progressive_to_date` instead of `work_progressive_previous`/`work_progressive_to_date`).
- **Verify**: Run exporter tests:
  `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py`

### Step 2: Update Valuation Summary Task Data Extraction
- **Files**: [tasks.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tasks.py)
- **Change**:
  - In `get_valuation_summary_data()`, skip line items where `item.addendum` is True.
  - Remove the virtual `"SPECIAL ITEMS"` section code block.
- **Verify**: Run summary data extraction tests:
  `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_get_valuation_summary_data`

### Step 3: Update Valuation Summary View
- **Files**: [payment_certificate_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/payment_certificate_views.py)
- **Change**:
  - In `PaymentCertificateValuationSummaryView.get_context_data()`, query and add `addendum_line_items` and `special_line_items` to the context dictionary.
- **Verify**: Compile views tests:
  `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py`

### Step 4: Create Reusable HTML Template Partial
- **Files**: [contractual_special_items.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/payment_certificate/tables/contractual_special_items.html) [NEW]
- **Change**:
  - Create a clean HTML table using standard styling.
  - Include three subsections: Addendum Line Items, Special Items, and Ledger Totals.
  - For each subsection, render rows with Description, Previous, Current, and Total.
  - Display subsection subtotals and table grand totals at the bottom.
- **Verify**: Verify file creation and template syntax.

### Step 5: Integrate Table in Django templates
- **Files**: 
  - [payment_certificate_detail.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/payment_certificate/payment_certificate_detail.html)
  - [view_detailed.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/payment_certificate/section_views/view_detailed.html)
  - [valuation_summary.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/payment_certificate/section_views/valuation_summary.html)
- **Change**:
  - In `payment_certificate_detail.html` and `view_detailed.html`, replace separate addendum, special items, and ledger totals sections with the unified table template.
  - In `valuation_summary.html`, include `contractual_special_items.html` below the main table, and update the Grand Total section of the page to sum BOQ totals and Contractual Special Items totals.
- **Verify**: Launch dev server and visually inspect screens.

### Step 6: Update PDF Detailed Template
- **Files**: [3-detailed.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/pdf_templates/valterra_rpm/3-detailed.html)
- **Change**:
  - Replace the separate tables for Addendum Line Items and Special Items with the unified "Contractual Special Items" table (styled cleanly for A4 landscape).
- **Verify**: Run PDF compile tests:
  `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf`

### Step 7: Update Excel Detailed Report Exporter
- **Files**: [detailed_report_exporter.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/exporters/detailed_report_exporter.py)
- **Change**:
  - Remove the addendum items append logic from standard structure sheets.
  - Rename sheet `"Special Items"` to `"Special Items"` (or keep as is) and render the unified "Contractual Special Items" table.
- **Verify**: Run Excel exporter tests:
  `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py`

### Step 8: Update Excel Summary Report Exporter
- **Files**: [summary_report_exporter.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/exporters/summary_report_exporter.py)
- **Change**:
  - Render the "Contractual Special Items" table below the main BOQ summary section.
  - Align columns with the main sheet (Description: Col 2, Previous: Col 5, Current: Col 6, Total: Col 4).
  - Update the Grand Total certified values at the bottom of the summary sheet.
- **Verify**: Run summary report exporter tests.

### Step 9: Add Verification Tests
- **Files**: [test_exporters.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_exporters.py)
- **Change**:
  - Add comprehensive test case assertions for the combined table structure, calculations, PDF outputs, and Excel sheets.
- **Verify**: `.venv\Scripts\python.exe -m pytest`

## Risks & mitigations
- **Risk**: Missing layout styling causing PDF overlap.
  - *Mitigation*: Ensure clean page breaks or borders are defined for the new table inside the PDF template.
- **Risk**: Ledger adjustments sign inversion.
  - *Mitigation*: Sum positive `amount` for list rows but use `signed_amount` for subtotals (matches current design).

## Rollback plan
- In case of issues, run:
  - `git checkout app/BillOfQuantities/exporters/`
  - `git checkout app/BillOfQuantities/models/`
  - `git checkout app/BillOfQuantities/templates/`
  - `git checkout app/BillOfQuantities/views/`
  - `git checkout app/BillOfQuantities/tasks.py`
  - `git checkout app/BillOfQuantities/tests/`
