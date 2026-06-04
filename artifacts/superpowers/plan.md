## Goal
Detect when an uploaded Excel sheet contains no valid line item rows, return a validation error to the user, and prevent deletion of existing database records.

## Assumptions
- The virtual environment is active.
- `import_boq_from_excel` in `app/BillOfQuantities/services.py` parses and validates Excel rows.
- Existing records are deleted only if no parsing errors were encountered.

## Plan
1. Step 1: Add a failing test case to `TestBOQExcelImporter` in `app/BillOfQuantities/tests/test_structure_views.py` that uploads a completely empty Excel sheet, asserts that the appropriate error is returned, and asserts that existing database structures/line items are NOT deleted.
   - Files: `app/BillOfQuantities/tests/test_structure_views.py`
   - Change: Add `test_import_empty_file_returns_error_and_does_not_delete` to verify empty file validation.
   - Verify: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py -k test_import_empty_file_returns_error_and_does_not_delete -v` (expected to fail)

2. Step 2: Implement the empty check in `import_boq_from_excel`.
   - Files: `app/BillOfQuantities/services.py`
   - Change: Check if `len(valid_forms) == 0` after the parsing loop. If so, return `0, ["Excel file is empty. Please ensure it contains at least one valid line item row."]`.
   - Verify: Run the test from Step 1 to ensure it passes.

3. Step 3: Run the full test suite and verify linting.
   - Files: None
   - Change: None
   - Verify: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py -v` and `.venv\Scripts\python.exe -m ruff check .`

## Risks & mitigations
- Risk: Users might actually want to delete all BOQ items by uploading an empty file.
- Mitigation: Uploading an empty file to delete data is highly error-prone and dangerous (a user might accidentally upload the wrong/empty template and wipe their BOQ). If deletion is needed, a separate dedicated deletion action should be provided.

## Rollback plan
- Revert changes using `git checkout app/BillOfQuantities/services.py app/BillOfQuantities/tests/test_structure_views.py`
