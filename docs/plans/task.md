# Task Progress: Report Selection and Configuration Customization

| Task ID | Task Description | Status | Verification Command / Method |
| :--- | :--- | :--- | :--- |
| **TSK-01** | Extend Project Model and Create Migration | `[x]` | `.venv\Scripts\python.exe -m pytest app/Project/tests/test_models.py -k test_project_has_report_configuration` |
| **TSK-02** | Build Report Configuration Form and Setup UI | `[x]` | `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -k test_project_setup_view_includes_layout_config` |
| **TSK-03** | Implement Dynamic Column Configuration in PDF Generation | `[x]` | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf_with_custom_columns` |
| **TSK-04** | Implement Dynamic Column Configuration in Excel Generation | `[x]` | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_excel_exporter_with_custom_columns` |
| **TSK-05** | Refactor Download PDF Reports Interface | `[x]` | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k TestDownloadViews` |
