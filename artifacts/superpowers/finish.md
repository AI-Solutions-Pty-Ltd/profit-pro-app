# Superpowers Implementation Finish Summary: Fix Excel BOQ Empty Upload Validation

## Summary of Changes
- **app/BillOfQuantities/services.py**: Added a validation check before the database deletion transaction in `import_boq_from_excel`. If `valid_forms` is empty (0 valid rows imported), it returns `0, ["Excel file is empty. Please ensure it contains at least one valid line item row."]` instead of performing a database delete operation.
- **app/BillOfQuantities/tests/test_structure_views.py**: Added the regression test `test_import_empty_file_returns_error_and_does_not_delete` to verify that empty uploads fail with the exact validation message and preserve existing database records.

## Verification Commands & Results
- Regression Test Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py -k test_import_empty_file_returns_error_and_does_not_delete -v` -> **PASSED**
- Full Test Suite Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py -v` -> **PASSED** (all 37 tests passing)
- Lint Check: `.venv\Scripts\python.exe -m ruff check app/BillOfQuantities/` -> **PASSED**
- Code Formatter: `.venv\Scripts\python.exe -m ruff format app/BillOfQuantities/` -> **PASSED**

## Review Pass
- **Blocker**: None.
- **Major**: None.
- **Minor**: None.
- **Nit**: None.

## Follow-ups / Manual Validation
- No further automated actions needed.
- Manual validation can be verified by attempting to upload a completely empty template or a template with formatted but empty cells: the page will correctly render with the validation error `"Excel file is empty. Please ensure it contains at least one valid line item row."`, and the project's existing BOQ structures will not be deleted.
