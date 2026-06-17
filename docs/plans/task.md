| Task ID | Task Description | Status | Verification Command / Method |
| :--- | :--- | :--- | :--- |
| **TSK-01** | Modify import BOQ service to skip formula-placeholder empty rows | [x] | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py::TestBOQExcelImporter::test_import_with_partially_empty_formula_rows -v` |

