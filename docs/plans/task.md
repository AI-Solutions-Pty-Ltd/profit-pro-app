# Task Progress: Fix Excel BOQ Empty Upload Validation

| Task ID | Task Description | Status | Verification Command / Method |
| :--- | :--- | :--- | :--- |
| **TSK-01** | Add regression test case `test_import_empty_file_returns_error_and_does_not_delete` to verify empty file uploads fail and preserve database records | `[x]` | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py -k test_import_empty_file_returns_error_and_does_not_delete -v` |
| **TSK-02** | Add empty check in `import_boq_from_excel` before database deletion transaction starts | `[x]` | View changes in `services.py` |
| **TSK-03** | Run full pytest test suite and ruff checks and formatting | `[x]` | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py -v` and `ruff check` |
