| Task ID | Task Description | Status | Verification Command / Method |
| :--- | :--- | :--- | :--- |
| **TSK-01** | Register new route in `app/Project/projects/project_urls.py` | [x] | `.venv\Scripts\python.exe manage.py check` |
| **TSK-02** | Implement `ProjectReportConfigView` view class in `app/Project/projects/project_views.py` | [x] | `.venv\Scripts\python.exe manage.py check` |
| **TSK-03** | Create the dedicated `report_config.html` template in `app/Project/templates/project/report_config.html` | [x] | Render checks and layout verification |
| **TSK-04** | Update project setup template in `app/Project/templates/project/project_setup.html` | [x] | Render checks on project setup page |
| **TSK-05** | Update and run unit views tests in `app/Project/tests/test_views.py` | [x] | `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py` |
