# Execution Notes: Customize Cover Page Report, Headers, and Titles

## Step 1: Update the Project model with `cover_page_config`
- **Files changed**: [projects_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/projects_models.py)
- **What changed**:
  - Added `cover_page_config` JSONField to `Project` model.
  - Implemented `get_cover_page_config()` method with a default structure and merge logic.
- **Verification command**: `.venv\Scripts\python.exe manage.py check`
- **Result**: PASS (System check identified no issues)

## Step 2: Generate and apply database migrations
- **Files changed**: `app/Project/migrations/0097_project_cover_page_config.py` (New auto-generated migration)
- **What changed**:
  - Generated Django database migration for `cover_page_config` JSONField.
  - Applied the migration to the database schema.
- **Verification command**: `.venv\Scripts\python.exe manage.py migrate`
- **Result**: PASS (Applying Project.0097_project_cover_page_config... OK)

## Step 3: Register URL pattern and add card in Project Setup page
- **Files changed**:
  - [project_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/project_urls.py)
  - [project_setup.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/project_setup.html)
- **What changed**:
  - Registered `<int:pk>/cover-config/` URL pattern for `ProjectCoverConfigView`.
  - Added "Payment Certificate Cover Page Setup" configuration card in the template setup grid.
- **Verification**: Verified registration (fails system check until view is implemented in Step 4, which is expected).

## Step 4: Create the Cover Page Configuration View
- **Files changed**: [project_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/project_views.py)
- **What changed**:
  - Implemented `ProjectCoverConfigView` handling GET and POST actions for cover page customizing.
- **Verification command**: `.venv\Scripts\python.exe manage.py check`
- **Result**: PASS (System check identified no issues)

## Step 5: Create the Config Template and Live Preview
- **Files changed**: [cover_config.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/cover_config.html) (New), [test_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_views.py)
- **What changed**:
  - Created `cover_config.html` containing form customization options and a live mockup preview.
  - Added unit test class `TestProjectCoverConfig` verifying GET template rendering and POST saving logic.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -v`
- **Result**: PASS (5 passed, 11 warnings)

## Step 6: Update the HTML Cover Page View
- **Files changed**:
  - [payment_certificate_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/payment_certificate_views.py)
  - [cover_page.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/payment_certificate/section_views/cover_page.html)
- **What changed**:
  - Added `cover_page_config` and flat `cover_fields` lookup dictionaries to context in `PaymentCertificateCoverPageView`.
  - Refactored `cover_page.html` to render customized section headings, titles, labels, and respect toggled visibilities.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_section_views.py -k TestPaymentCertificateCoverPageView -v`
- **Result**: PASS (6 passed, 15 deselected)

## Step 7: Update the PDF Cover Page Template
- **Files changed**:
  - [tasks.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tasks.py)
  - [1-front-page.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/pdf_templates/valterra_rpm/1-front-page.html)
- **What changed**:
  - Passed `cover_page_config` and `cover_fields` to rendering context in `compile_pdf_for_certificate`.
  - Refactored `1-front-page.html` to dynamically look up customized labels, titles, and conditionally render visible fields.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf -v`
- **Result**: PASS (7 passed, 5 deselected)

## Step 8: Update the Excel Cover Page Exporter
- **Files changed**:
  - [cover_page_exporter.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/exporters/cover_page_exporter.py)
- **What changed**:
  - Retrieved custom `cover_page_config` matching defaults or project customizations.
  - Refactored Sections A, B, and C to dynamically shift row index counters (`current_row`) based on fields' visibility.
  - Displayed custom field labels for active fields and bypassed output for disabled fields.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -v`
- **Result**: PASS (12 passed, 83 warnings)

## Step 9: Add Verification Tests
- **Files changed**:
  - [test_exporters.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_exporters.py)
  - [test_payment_certificate_section_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_payment_certificate_section_views.py)
- **What changed**:
  - Added `test_cover_page_custom_config` in `test_exporters.py` to assert custom cover configuration titles, headers, and disabled fields in Excel exports and PDF outputs.
  - Added `test_cover_page_custom_config_rendering` in `test_payment_certificate_section_views.py` to verify customized headers and visibilities in the browser HTML cover page.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py app/BillOfQuantities/tests/test_payment_certificate_section_views.py -v`
- **Result**: PASS (35 passed, 273 warnings)
# Phase 2 Execution Notes: Reorder Custom Labels and Sections

## Step 1: Update get_cover_page_config resolution in the Project model
- **Files changed**:
  - [projects_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/projects_models.py)
- **What changed**:
  - Added support for top-level `"section_order"` resolving to custom sequence or defaulting.
  - Updated field resolution loop to preserve custom field ordering and append missing default fields at the end.
- **Verification command**: `.venv\Scripts\python.exe manage.py check`
- **Result**: PASS (System check identified no issues)

## Step 2: Implement a helper to resolve cover page sections and fields with values
- **Files changed**:
  - [payment_certificate_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/payment_certificate_views.py)
- **What changed**:
  - Implemented `get_resolved_cover_page_sections(payment_certificate)` helper function.
  - Calculated Section A metadata, Section B values, and Section C values (including special items) inside Python.
  - Added style flags (`is_bold`, `is_italic_gray`, `is_status`, `is_mono`) to allow uniform rendering across templates.
- **Verification command**: `.venv\Scripts\python.exe manage.py check`
- **Result**: PASS (System check identified no issues)

## Step 3: Update browser HTML Cover Page view
- **Files changed**:
  - [payment_certificate_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/payment_certificate_views.py)
  - [cover_page.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/payment_certificate/section_views/cover_page.html)
- **What changed**:
  - Added `ordered_sections` context variable in `PaymentCertificateCoverPageView`.
  - Refactored `cover_page.html` to dynamically loop over the ordered sections and fields, applying tailwind layout styles and status badges dynamically based on style tags.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_section_views.py -v`
- **Result**: PASS (22 passed)

## Step 4: Update PDF Cover Page compilation
- **Files changed**:
  - [tasks.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tasks.py)
  - [1-front-page.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/pdf_templates/valterra_rpm/1-front-page.html)
- **What changed**:
  - Resolved `ordered_sections` context using `get_resolved_cover_page_sections` in `tasks.py`.
  - Refactored `1-front-page.html` to dynamically render Section A as metadata list and Sections B & C as structured tables ordered by custom section ordering.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf -v`
- **Result**: PASS (7 passed)
## Step 5: Update Excel Cover Page exporter
- **Files changed**: [cover_page_exporter.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/exporters/cover_page_exporter.py)
- **What changed**:
  - Refactored `export_cover_page_to_xlsx` to dynamically iterate through `section_order` and write Excel sections in the customized sequence.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py::TestExporters::test_cover_page_custom_config -v`
- **Result**: PASS

## Step 6: Implement UI reordering controls in `cover_config.html`
- **Files changed**: [cover_config.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/cover_config.html)
- **What changed**:
  - Added Up/Down section reordering buttons to the accordion headers.
  - Added Up/Down field reordering buttons to the actions column in the fields tables.
  - Wrote JS logic to dynamically swap sections/fields in memory, update the DOM hierarchy, update the live preview mockup, and serialize order configuration to JSON input.
  - Handled stop propagation on accordion headers so clicking reorder buttons does not toggle them.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -v`
- **Result**: PASS

## Step 7: Add Verification Tests
- **Files changed**: [test_exporters.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_exporters.py)
- **What changed**:
  - Implemented `test_cover_page_custom_ordering` in `TestExporters` class.
  - Configured custom section order (`section_c`, `section_a`, `section_b`) and custom field orders.
  - Asserted correct sequence positions of section titles and custom field labels in compiled openpyxl Excel spreadsheet output.
  - Verified PDF compiled successfully without rendering errors.
- **Verification command**: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_cover_page_custom_ordering -v`
- **Result**: PASS

## Step 8: Code Quality & Lint Pass
- **Files changed**: [test_exporters.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_exporters.py)
- **What changed**:
  - Ran `ruff check` on modified python files.
  - Ran `ruff format` to auto-reformat code layout to match ruff formatting conventions.
- **Verification command**: `.venv\Scripts\python.exe -m ruff check app/BillOfQuantities/tests/test_exporters.py`
- **Result**: PASS
