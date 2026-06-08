# Superpowers Execution Log: Report Selection and Configuration Customization

## Task 1: Extend Project Model and Create Migration
- **Files changed**:
  - `app/Project/projects/projects_models.py`
  - `app/Project/tests/test_models.py`
  - `app/Project/migrations/0090_project_column_config_and_more.py`
- **What changed**:
  - Added choice `LEPHADIMISHA` to `CertificateLayout` enum and `column_config` JSONField to the `Project` model.
  - Implemented `get_column_config` helper to return the resolved column configuration, supporting defaults and fallback layout overrides (e.g. for LEPHADIMISHA layout).
  - Configured `save` method to invalidate cached PDFs when `certificate_layout` changes.
  - Added unit test `test_project_has_report_configuration` to test_models.py.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_models.py -k test_project_has_report_configuration`
- **Result**: PASS

## Task 2: Build Report Configuration Form and Setup UI
- **Files changed**:
  - `app/Project/projects/project_views.py`
  - `app/Project/templates/project/project_setup.html`
  - `app/Project/tests/test_views.py`
- **What changed**:
  - Added handling of `save_report_config` POST action in `ProjectSetupView`.
  - Serialized `project_columns_json` in project setup template context.
  - Created Report Layout card in `project_setup.html` with vanilla JS config engine supporting sortable up/down ordering, renaming, visibility toggle, and live mock header preview table.
  - Added test case `test_save_report_config_success` in `app/Project/tests/test_views.py`.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -k test_save_report_config_success`
- **Result**: PASS

## Task 3: Implement Dynamic Column Configuration in PDF Generation
- **Files changed**:
  - `app/BillOfQuantities/tasks.py`
  - `app/BillOfQuantities/templates/pdf_templates/line_items_table.html`
  - `app/BillOfQuantities/tests/test_exporters.py`
- **What changed**:
  - Retrieved `project.get_column_config()` in `compile_pdf_for_certificate` and injected the active columns list into the rendering context.
  - Rewrote `line_items_table.html` to dynamically render headers, spacers, data cells, and footer totals based on the active columns and custom labels.
  - Wrote TDD test `test_compile_pdf_with_custom_columns` in `test_exporters.py` to assert custom headers are rendered and disabled ones are omitted.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf_with_custom_columns -v`
- **Result**: PASS

## Task 4: Implement Dynamic Column Configuration in Excel Generation
- **Files changed**:
  - `app/BillOfQuantities/exporters/excel_exporter.py`
  - `app/BillOfQuantities/tests/test_exporters.py`
- **What changed**:
  - Imported `get_column_letter` utility.
  - Retrieved active columns and mapped each column `id` to its index and Excel letter coordinate.
  - Rewrote sheet generation, headers, cell widths, cell values, and subtotal SUM formulas to resolve coordinate letters dynamically.
  - Added TDD test `test_excel_exporter_with_custom_columns` in `test_exporters.py` to assert custom header names and dynamic multiplication formulas (e.g. `=B6*C6`).
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_excel_exporter_with_custom_columns -v`
- **Result**: PASS

## Task 5: Refactor Download PDF Reports Interface
- **Files changed**:
  - `app/BillOfQuantities/templates/payment_certificate/payment_certificate_detail.html`
- **What changed**:
  - Refactored JavaScript polling function `updatePDFStatus()` to target the correct button ID (`#full-pdf-button` or `#abridged-pdf-button`) explicitly, preventing accidental styling/disabling of Excel download buttons.
  - Used `classList` add/remove operations in JavaScript to preserve layout/width styling of buttons when changing state.
  - Updated force regenerate checkbox event listeners to toggle button text dynamically between 'Download PDF' and 'Regenerate PDF'.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k TestDownloadViews -v`
- **Result**: PASS

