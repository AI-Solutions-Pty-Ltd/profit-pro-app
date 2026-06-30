# Custom Project Groups and Regional Reports Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Implement custom project grouping (favorites/named groups) and generate cover page and valuation summary reports structured by province.

**Architecture:** Create `ProjectGroup` database model. Formulate group creation AJAX view, UI modal, header navigation, HTML report views, and openpyxl XLSX exporters.

**Tech Stack:** Django, Python, openpyxl, Tailwind CSS, Javascript/AJAX.

---

### Task 1: ProjectGroup Model implementation
**Files:**
- Modify: `app/Project/projects/projects_models.py`
- Modify: `app/Project/models/__init__.py`
- Modify: `app/Project/admin.py`

**Steps:**
1. Declare `ProjectGroup` model in `projects_models.py` inheriting from `BaseModel`.
2. Import `ProjectGroup` in `models/__init__.py`.
3. Register `ProjectGroup` in `admin.py`.
4. Run migrations: makemigrations and migrate.

### Task 2: Project Management UI updates
**Files:**
- Modify: `app/Project/templates/project/project_list.html`
- Modify: `app/Project/projects/project_views.py:63-110`

**Steps:**
1. In `project_views.py` `ProjectListView.get_context_data`, inject user's active project groups: `context['project_groups'] = self.request.user.project_groups.filter(deleted=False)`.
2. In `project_list.html` header, add a dropdown next to the back button listing saved project groups and view/delete routes.
3. In `project_list.html`, add a modal for creating groups.
4. Add a "Create Group" button in the batch action bar.
5. In `project_list.html`, write Javascript logic to open the modal, make the AJAX POST request, show validation errors, and redirect on success.

### Task 3: URL Routing configuration
**Files:**
- Modify: `app/Project/urls/portfolio_urls.py`

**Steps:**
1. Append the URL routes for group creation, deletion, cover-page, cover-page-xlsx, valuation-summary, and valuation-summary-xlsx.

### Task 4: View Controllers implementation
**Files:**
- Modify: `app/Project/views/portfolio_views.py`

**Steps:**
1. Implement `ProjectGroupCreateView` and `ProjectGroupDeleteView` handling soft delete.
2. Implement `GroupCoverPageView` and `GroupValuationSummaryView` (calculating province-level groupings and sub-totals).
3. Implement `GroupCoverPageDownloadXLSXView` and `GroupValuationSummaryDownloadXLSXView`.

### Task 5: Regional Exporters (XLSX)
**Files:**
- Create: `app/BillOfQuantities/exporters/group_summary_report_exporter.py`

**Steps:**
1. Implement the regional XLSX exporter for the valuation summary, grouping by province with header rows, project rows, province sub-totals, and grand totals.

### Task 6: HTML views and templates
**Files:**
- Create: `app/Project/templates/portfolio/reports/group_cover_page.html`
- Create: `app/Project/templates/portfolio/reports/group_valuation_summary.html`

**Steps:**
1. Create the cover page HTML template.
2. Create the regional valuation summary HTML template showing province headers and sub-totals.

### Task 7: Unit Testing and Verification
**Files:**
- Modify: `app/Project/tests/factories.py`
- Create: `app/Project/tests/test_project_groups.py`

**Steps:**
1. Add `ProjectGroupFactory` to `factories.py`.
2. Write unit tests in `test_project_groups.py` testing creation, duplication error, deletion, views, sub-totals rendering, and downloads.
3. Run all tests and verify exit status.
