| Task ID | Task Description | Status | Verification Command / Method |
| :--- | :--- | :--- | :--- |
| **TSK-01** | Create tests for `space_intcomma` filter | [x] | `.venv\Scripts\python.exe -m pytest app/core/tests/test_template_extras.py` |
| **TSK-02** | Implement `space_intcomma` template filter | [x] | `.venv\Scripts\python.exe -m pytest app/core/tests/test_template_extras.py` |
| **TSK-03** | Apply `space_intcomma` to Valterra RPM PDF front page | [x] | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py` |
| **TSK-04** | Apply `space_intcomma` to Valterra RPM PDF summary and detailed pages | [x] | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py` |
| **TSK-05** | Apply `space_intcomma` to Standard PDF layout pages | [x] | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py` |
| **TSK-06** | Replace hardcoded signatories with allocated project signatories in `valterra_rpm/1-front-page.html` | [x] | View file modification & compile test |
| **TSK-07** | Add and run test cases for signatories rendering in `test_exporters.py` | [x] | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py` |
| **TSK-08** | Update Excel exporters footer branding to "Sedgepro" | [x] | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py` |
| **TSK-09** | Update standard layout signatories in `3-footer.html` | [x] | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py` |
| **TSK-10** | Add Sedgepro running footer to all PDF templates | [x] | Verify PDF renders and footers are displayed |
| **TSK-11** | Implement report naming helper and update view file downloads | [x] | Test filename output formatting |
| **TSK-12** | Add `disciplines` Many-to-Many field to `Company` model | [x] | Run makemigrations and verify new fields |
| **TSK-13** | Create and apply migrations (schema & data migration for 13 disciplines) | [x] | `.venv\Scripts\python.exe manage.py migrate` |
| **TSK-14** | Update forms (`CompanyForm` & `ConsultantCompanyForm`) to support multiple disciplines | [x] | Verify form validation and field popping |
| **TSK-15** | Update template `lead_consultant_form.html` with select and badges/pills JS UI | [x] | Visual check in browser / manual test |
| **TSK-16** | Define factories and write unit tests for multiple disciplines | [x] | `.venv\Scripts\python.exe -m pytest app/Project/tests/test_forms.py` |
| **TSK-17** | Set `tax_number` as explicitly optional in `CompanyForm` | [x] | Run pytest tests |
| **TSK-18** | Hide `tax_number` from `lead_consultant_form.html` | [x] | Visual check / template inspection |
| **TSK-19** | Fix lock alignment globally by wrapping inputs in relative container | [x] | Visual check / JS verification |
