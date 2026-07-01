# Multi-Project Selection and Reports Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Implement checkboxes on the Project Management page to allow selecting multiple projects, then dynamically aggregate and view Cover Page and Valuation Summary reports.

**Architecture:** Use query parameters `?project_ids=1,2,3` to transfer selected IDs to dynamic Django views, checking permissions and aggregating latest approved payment certificates.

**Tech Stack:** Django, Python, openpyxl, Tailwind CSS.

---

### Task 1: Checkboxes and Batch Action Bar UI
**Files:**
- Modify: `app/Project/templates/project/project_list.html`

**Steps:**
1. Add a select-all checkbox in the table header.
2. Add checkboxes in each project row.
3. Append a floating batch action bar at the bottom with counts and view buttons.
4. Add Javascript to toggle checkboxes, update counts, and handle redirects using `?project_ids=1,2,3`.

### Task 2: URL Routing configuration
**Files:**
- Modify: `app/Project/urls/portfolio_urls.py`

**Steps:**
1. Append the URL routes for multi-project cover-page, cover-page-xlsx, valuation-summary, and valuation-summary-xlsx.

### Task 3: Aggregated XLSX Exporters
**Files:**
- Create: `app/BillOfQuantities/exporters/multi_project_cover_page_exporter.py`
- Create: `app/BillOfQuantities/exporters/multi_project_summary_report_exporter.py`

**Steps:**
1. Implement the cover page exporter using openpyxl, aggregating selected project IDs.
2. Implement the summary report exporter listing each project as a row and summing column totals.

### Task 4: View Controllers implementation
**Files:**
- Modify: `app/Project/views/portfolio_views.py`

**Steps:**
1. Implement `MultiProjectCoverPageView` and `MultiProjectValuationSummaryView`.
2. Implement download views `MultiProjectCoverPageDownloadXLSXView` and `MultiProjectValuationSummaryDownloadXLSXView`.

### Task 5: HTML Views Templates
**Files:**
- Create: `app/Project/templates/portfolio/reports/multi_project_cover_page.html`
- Create: `app/Project/templates/portfolio/reports/multi_project_valuation_summary.html`

**Steps:**
1. Create the aggregated cover page HTML template.
2. Create the aggregated valuation summary HTML template.

### Task 6: Unit Testing and Verification
**Files:**
- Create: `app/Project/tests/test_multi_project_reports.py`

**Steps:**
1. Write unit tests covering listing redirects, HTML views loading, and XLSX spreadsheet downloads.
2. Verify all tests pass.
