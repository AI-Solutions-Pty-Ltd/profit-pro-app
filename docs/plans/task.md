| Task ID | Task Description | Status | Verification Command / Method |
| :--- | :--- | :--- | :--- |
| **TSK-01** | Statically Remove List Validation from Excel Template | [x] | `.venv\Scripts\python.exe -c "import openpyxl; wb=openpyxl.load_workbook('app/BillOfQuantities/data/Project set-up Template.xlsx'); ws=wb['Setup Template']; assert len(ws.data_validations.dataValidation) == 2"` |
| **TSK-02** | Add Test to Verify Downloaded Template has no Unit Validation List | [x] | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py::TestDownloadBOQTemplateView::test_downloaded_template_has_no_unit_validation -v` |
