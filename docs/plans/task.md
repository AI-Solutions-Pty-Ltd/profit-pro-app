| Task ID | Task Description | Status | Verification Command / Method |
| :--- | :--- | :--- | :--- |
| **TSK-01** | Update Download BOQ Template View | [x] | `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py::TestDownloadBOQTemplateView::test_download_success -v` |
| **TSK-02** | Update ProjectDocument.upload_to for BOQ category | [x] | `.venv\Scripts\python.exe -m pytest app/Project/tests/test_models.py -v` |
| **TSK-03** | Overwrite Filename header in secure media serving for downloads | [/] | `.venv\Scripts\python.exe -m pytest app/core/tests/test_media_serving.py -v` |
