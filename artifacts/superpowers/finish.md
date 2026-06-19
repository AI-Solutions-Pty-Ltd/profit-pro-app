# Final Summary: Special Items in Payment Certificate Reports and Views

All steps in the implementation plan have been completed and verified successfully.

## Review Pass
- **Blocker**: None.
- **Major**: None.
- **Minor**: None.
- **Nit**: None.

## Verification Commands & Results
The following test suites were run and passed successfully:
1. `pytest app/BillOfQuantities/tests/test_exporters.py -k test_get_valuation_summary_data` (Valuation Summary groupings/totals) -> **PASS**
2. `pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf_for_certificate` (PDF template compilation) -> **PASS**
3. `pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf_abridged` (Abridged PDF templates) -> **PASS**
4. `pytest app/BillOfQuantities/tests/test_exporters.py -k test_special_items_exporters` (Verification of calculations on all 3 item types under PDF/Excel exporters) -> **PASS**
5. `pytest app/BillOfQuantities/tests/test_exporters.py` (Full exporter test suite of 12 tests) -> **PASS**
6. Code linting and formatting check: `ruff check` and `ruff format` -> **PASS**

## Summary of Changes

### 1. Valuation Summary Task Data
- Grouped Contractual Special Items (`LineItem` with `special_item=True, addendum=False`) into a virtual section named `"SPECIAL ITEMS"` at the end of the summary.
- Constructed a virtual bill for each special item row.
- Ensured total budget, cumulative, previous, and current sums are updated dynamically to include special items.

### 2. PDF Context & Rendering
- Separated queries in `compile_pdf_for_certificate()` to map normal contract items, addendum items, and special items individually.
- Rendered clean tables for both Addendum items and Special items in `3-detailed.html` with correct page breaks.
- Realigned `1-front-page.html` (cover page) to show correct mathematical rows matching the HTML cover page, including the loop over active special items.

### 3. Excel Exporters
- Updated `detailed_report_exporter.py` to filter contract items on standard structure sheets, append structure-related addendums at the bottom of the corresponding sheet under sub-headers, and output special items on a dedicated `"Special Items"` sheet.
- Updated `cover_page_exporter.py` to calculate and output the exact breakdown (work done up to assessment, contract/addendum compensation events, special items loop, net certified amount, VAT, and total).

### 4. Verification Tests
- Added `test_special_items_exporters` in `test_exporters.py` to verify the accuracy of calculations on certificates containing standard, addendum, and special items across PDF and Excel exporters.

## Manual Validation Steps
If verifying manually in the web application interface:
1. Go to the **Valuation** page of a Payment Certificate.
2. Ensure Special Items are correctly listed at the bottom under the virtual summary section `"SPECIAL ITEMS"`.
3. Check the **Cover Page** view to ensure the totals correctly include standard items, addendum items, and special items.
4. Download the **Detailed Report PDF**, **Valuation Summary Excel**, and **Detailed Report Excel**. Verify:
   - The Excel Detailed Report contains a dedicated sheet named `"Special Items"`.
   - The Excel Cover Page totals match the PDF Cover Page totals exactly.
