## Goal
Create a dedicated Column Heading Customization & Reordering page, replace the table/form under "Report Selection & Configuration" in the project setup page with a "Report Template Setup" card, and add a link/button on that card to access the new dedicated page.

## Assumptions
- The database schema for storing column configurations does not change (stored as a JSON field in `project.column_config`).
- Project permission requirements for the new page are identical to the setup page (`Role.USER` of the project).
- Virtual environment `.venv` is available and runs Python 3.11+.

## Plan

### 1. Register new route
- **Files**: `app/Project/projects/project_urls.py`
- **Change**: Add a new path `<int:pk>/report-config/` mapped to `project_views.ProjectReportConfigView.as_view()` with route name `project-report-config`.
- **Verify**: Run `.venv\Scripts\python.exe manage.py check` to check route mapping correctness.

### 2. Implement `ProjectReportConfigView` view class
- **Files**: `app/Project/projects/project_views.py`
- **Change**: Define `ProjectReportConfigView` view class inheriting from `ProjectMixin` and `DetailView`. Implement breadcrumbs leading back to setup page, context data (providing `project_columns_json`), and POST handler for `save_report_config` action.
- **Verify**: Run `.venv\Scripts\python.exe manage.py check` to make sure python files compile cleanly.

### 3. Create the dedicated `report_config.html` template
- **Files**: `app/Project/templates/project/report_config.html`
- **Change**: Create a new template containing the column configuration table, live preview table, form with CSRF token, and the interactive drag/reorder Javascript logic.
- **Verify**: Ensure the template renders with appropriate Tailwind utility classes and contains matching element IDs for the Javascript script block.

### 4. Update project setup template
- **Files**: `app/Project/templates/project/project_setup.html`
- **Change**: Remove the column customization form and its script block. Insert a new "Report Template Setup" card under the "Report Selection & Configuration" section, linking to the new page.
- **Verify**: Ensure the setup page loads without syntax errors.

### 5. Update and run unit tests
- **Files**: `app/Project/tests/test_views.py`
- **Change**: Modify tests in `TestProjectSetupReportConfig` to test `project:project-report-config` GET and POST methods instead of the setup view.
- **Verify**: Run `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py` to ensure tests pass successfully.

## Risks & mitigations
- **Risk**: Javascript elements (like table lists) fail to load or error out on elements that were omitted.
  - *Mitigation*: Ensure all required IDs (`columns-config-list`, `live-header-preview`, `live-body-preview`, `column-config-input`, `report-config-form`, `reset-columns-btn`) are fully preserved in `report_config.html`.
- **Risk**: User attempts to customize reports for a project they do not belong to.
  - *Mitigation*: Inheriting from `ProjectMixin` enforces correct project access roles and subscription checks.

## Rollback plan
- Revert all modified files to their previous Git commit state: `git checkout app/Project/`
- Delete `app/Project/templates/project/report_config.html`.
