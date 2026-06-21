| Task ID | Task Description | Status | Verification Command / Method |
| :--- | :--- | :--- | :--- |
| **TSK-01** | Modify import BOQ service to skip formula-placeholder empty rows | [x] | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py::TestBOQExcelImporter::test_import_with_partially_empty_formula_rows -v` |
| **TSK-02** | Brainstorm report column heading reordering | [x] | Verify brainstorm.md exists in artifacts/superpowers/ |
| **TSK-03** | Fix reorder icon SVG rendering on Report Column Customization page | [x] | Verify the gray Up/Down chevron icons show correctly in Actions column |
| **TSK-04** | Clean up test_views.py to remove temporary debug failing test | [x] | `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -v` |
| **TSK-05** | Restyle customization page using DaisyUI and Heroicons, push and create PR | [x] | Verify PR #266 is created to develop |
| **TSK-06** | Clean up temporary edit in get_ledger_summary_items | [x] | Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_models.py` |
| **TSK-07** | Update Current Certificate Ledger Helper Methods | [x] | Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_models.py -k test_current_ledger_totals_with_debits_and_credits` |
| **TSK-08** | Update Previous Certificates Ledger Properties | [x] | Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_models.py -k test_previous_ledger_totals_with_debits_and_credits` |
| **TSK-09** | Clean up `credits` variable shadowing in `payment_certificate_models.py` | [x] | Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_models.py` |
| **TSK-10** | Pre-select and disable `payment_certificate` in `ledger_forms.py` | [x] | Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_views.py` |
| **TSK-11** | Pre-select and disable `payment_certificate` on SpecialItem forms in `ledger_views.py` | [x] | Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_special_item_views.py` |
| **TSK-12** | Update Project model with `cover_page_config` and default schema | [x] | Run: `.venv\Scripts\python.exe manage.py check` |
| **TSK-13** | Generate and apply database migrations for cover page config | [x] | Run makemigrations and migrate |
| **TSK-14** | Register URL pattern and add card in Project Setup page | [x] | Verify setup page URL |
| **TSK-15** | Implement ProjectCoverConfigView view | [x] | Run view tests |
| **TSK-16** | Create the cover_config.html customization template with live preview | [x] | Verify rendering of template |
| **TSK-17** | Update HTML browser cover page view to respect cover_page_config | [x] | Check cover page layout |
| **TSK-18** | Update PDF cover page template (1-front-page.html) to respect config | [x] | Run PDF compilation tests |
| **TSK-19** | Update Excel exporter (cover_page_exporter.py) with dynamic rows and labels | [x] | Run Excel export tests |
| **TSK-20** | Add comprehensive unit tests verifying custom cover page config output | [x] | Run pytest on exports |
| **TSK-21** | Update get_cover_page_config resolution in the Project model | [x] | Run django check |
| **TSK-22** | Implement a helper to resolve cover page sections and fields with values | [x] | Run syntax checks |
| **TSK-23** | Update browser HTML Cover Page view | [x] | Run pytest on cover views |
| **TSK-24** | Update PDF Cover Page compilation | [x] | Run PDF compilation tests |
| **TSK-25** | Update Excel Cover Page exporter | [x] | Run Excel export tests |
| **TSK-26** | Add reordering controls to Customization Page | [x] | Manually verify reordering |
| **TSK-27** | Add Verification Tests | [x] | Run all pytest suites |
| **TSK-28** | Update get_resolved_cover_page_sections in payment_certificate_views.py | [x] | Run django check |
| **TSK-29** | Update browser HTML template cover_page.html | [x] | Run pytest on views |
| **TSK-30** | Update Excel exporter cover_page_exporter.py | [x] | Run pytest on exporters |
| **TSK-31** | Update JS Live Preview in cover_config.html | [x] | Verify live mockup preview |
| **TSK-32** | Add tests and verify | [x] | Run all pytest suites |
