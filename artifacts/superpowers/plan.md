## Goal
Update the detailed payment certificate Excel download to use `03_MediaCentre_Detailed.xlsx` as the template layout.

## Assumptions
- The template file `03_MediaCentre_Detailed.xlsx` will be moved to `app/BillOfQuantities/templates/excel/` for better organization.
- `openpyxl` can load the template without losing complex formatting.
- The structure of the generated Excel should be one sheet per Structure, based on the template sheet.

## Plan
1. **File**: `app/BillOfQuantities/exporters/excel_exporter.py`
   **Change**: Modify `generate_payment_certificate_excel` to:
   - Load `03_MediaCentre_Detailed.xlsx` as a workbook using `openpyxl.load_workbook`.
   - Identify the base template sheet.
   - For each Structure in the project, copy the template sheet.
   - Inject project details (name, cert no, date) into the specific header cells.
   - Iterate through line items and write values into the correct columns matching the template.
   - Delete the original template sheet before returning the workbook.
   **Verify**: Check for syntax errors by running `.venv\Scripts\python.exe -m ruff check app/BillOfQuantities/exporters/excel_exporter.py`.

2. **File**: `c:\Users\nebst\Projects\profit-pro-app`
   **Change**: Move `03_MediaCentre_Detailed.xlsx` into `app/BillOfQuantities/templates/excel_templates/` so it is packaged correctly.
   **Verify**: Ensure the file exists at the new path.

3. **File**: `app/BillOfQuantities/tests/test_exporters.py` (or similar)
   **Change**: Add or update a test to verify that the generated Excel contains the new sheets and headers.
   **Verify**: Run `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/` to confirm.

## Risks & mitigations
- **Risk**: `openpyxl` dropping styles when copying sheets. **Mitigation**: Manually re-apply critical styles if they drop, or use the template sheet directly for the first structure and copy it for subsequent ones.
- **Risk**: Formula calculation errors. **Mitigation**: Ensure formulas in the total/summary rows correctly reference the dynamically inserted row indices.

## Rollback plan
Revert `app/BillOfQuantities/exporters/excel_exporter.py` to its previous state (git checkout) and move the template file back if necessary.
