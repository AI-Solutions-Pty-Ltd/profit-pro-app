# Task Progress: Fix Payment Certificate PDF Download 404 Error

| Task ID | Task Description | Status | Verification Command / Method |
| :--- | :--- | :--- | :--- |
| **TSK-01** | Add reproduction/regression test cases for PDF download views (superuser & project role users) | `[x]` | View the test file and check for new test assertions |
| **TSK-02** | Remove incorrect `project__users=request.user` query filter from the download, abridged download, status, and email views | `[x]` | View changes in `payment_certificate_views.py` |
| **TSK-03** | Run the pytest suite to verify all payment certificate views tests pass | `[x]` | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_payment_certificate_views.py -v` |
