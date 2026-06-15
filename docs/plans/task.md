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

