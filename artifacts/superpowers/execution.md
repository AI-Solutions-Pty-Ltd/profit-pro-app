# Execution Notes - Special Items in Payment Certificate Reports and Views

### Step 1: Update Valuation Summary data extraction
- **Files changed**: `app/BillOfQuantities/tasks.py`
- **What changed**:
  - Updated `get_valuation_summary_data()` to filter for contractual special items (`special_item=True, addendum=False`).
  - Added logic to construct a virtual `"SPECIAL ITEMS"` section containing each special item description as a bill row.
  - Appended this virtual section to `grouped_sections` and updated total sums dynamically.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_get_valuation_summary_data`
- **Result**: PASS

### Step 2: Separate line item types in PDF compilation task
- **Files changed**: `app/BillOfQuantities/tasks.py`
- **What changed**:
  - Updated `compile_pdf_for_certificate()` to separate contract, addendum, and special items into `grouped_line_items`, `addendum_items`, and `special_items` for both full and abridged modes.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf_for_certificate`
- **Result**: PASS

### Step 3: Add Addendum and Special Items tables to Detailed Report PDF
- **Files changed**: `app/BillOfQuantities/templates/pdf_templates/valterra_rpm/3-detailed.html`, `app/BillOfQuantities/models/payment_certificate_models.py`
- **What changed**:
  - Added `special_items_budget_total` property to `PaymentCertificate` model to retrieve the sum of special items' budgets.
  - Updated detailed report template `3-detailed.html` to render separate `Addendum Line Items` and `Special Items` tables under their own page breaks and title sections.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf_abridged`
- **Result**: PASS

### Step 4: Refactor Excel Detailed Report Exporter
- **Files changed**: `app/BillOfQuantities/exporters/detailed_report_exporter.py`
- **What changed**:
  - Filtered line items into contract, addendum, and special items.
  - Appended structure-related addendums at the bottom of their respective sheets under sub-headers.
  - Created a dedicated "Special Items" sheet listing special items directly with a total row.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py`
- **Result**: PASS

### Step 5: Update Excel Cover Page Exporter
- **Files changed**: `app/BillOfQuantities/exporters/cover_page_exporter.py`
- **What changed**:
  - Rebuilt `payment_rows` to display previous work done, compensation events, and addendum events.
  - Included a dynamic loop over `special_items_annotated` to list active special items.
  - Updated totals, net amount due, VAT, and final certified sum calculations to match the HTML cover page.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py`
- **Result**: PASS

### Step 6: Update PDF Cover Page Template
- **Files changed**: `app/BillOfQuantities/templates/pdf_templates/valterra_rpm/1-front-page.html`
- **What changed**:
  - Loaded `mathfilters` and `humanize` template tags.
  - Aligned the cover page rows to display previous work done, contract compensation events, addendum compensation events, and a dynamic loop over annotated special items.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py`
- **Result**: PASS

### Step 7: Add new verification tests for Special Items calculations
- **Files changed**: `app/BillOfQuantities/tests/test_exporters.py`
- **What changed**:
  - Added `test_special_items_exporters` verifying standard, addendum, and special items calculations, PDF rendering, and Excel sheets structure.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py`
- **Result**: PASS
