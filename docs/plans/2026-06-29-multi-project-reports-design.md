# Design Document — Multi-Project Selection and Reports

This document outlines the design for allowing users to select multiple projects from the Project Management page and view their aggregated Cover Page and Valuation Summary.

## 1. User Interface
- Add a checkbox column to the Project list table in `project_list.html`.
- Implement a floating batch actions bar styled with modern glassmorphism that slides up from the bottom of the viewport when projects are selected.
- Provide buttons to view Cover Page and Valuation Summary.
- JavaScript extracts selected IDs and redirects to reporting URLs with `?project_ids=1,2,3`.

## 2. URL Routes
Add the following URL routes under `app/Project/urls/portfolio_urls.py`:
- `reports/multi/cover-page/` -> `MultiProjectCoverPageView`
- `reports/multi/cover-page/xlsx/` -> `MultiProjectCoverPageDownloadXLSXView`
- `reports/multi/valuation-summary/` -> `MultiProjectValuationSummaryView`
- `reports/multi/valuation-summary/xlsx/` -> `MultiProjectValuationSummaryDownloadXLSXView`

## 3. View Logic & Scoping
- Retrieve `project_ids` parameter from `request.GET`.
- Filter and authenticate: only allow active projects that the logged-in user has permission to view.
- Retrieve the latest approved `PaymentCertificate` for each authorized project.
- Aggregate contract values and certificate metrics.

## 4. Excel Exporters
- `multi_project_cover_page_exporter.py`: Aggregate metrics across selected projects and render cover page.
- `multi_project_summary_report_exporter.py`: Create valuation summary listing each project as a row and summing totals.
