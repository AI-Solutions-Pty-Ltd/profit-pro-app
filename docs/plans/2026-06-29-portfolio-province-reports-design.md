# Design Document: Portfolio Cover Page & Valuation Summary Grouped by Province

## Goal
Enable users to view, group, and download/export aggregated Cover Page and Valuation Summary reports by Province directly from the Portfolio Dashboard page.

## Proposed Architecture

### 1. Tab Integration
We will add a new tab, **Province Summary**, to the reports navigation header `app/Project/templates/portfolio/reports_nav.html`. When clicked, it will navigate to a new view that displays a table of provinces with project counts and action links.

### 2. URL Routing
We will add the following URLs in `app/Project/urls/portfolio_urls.py`:
*   `/portfolio/reports/province/` &rarr; `portfolio-province-summary`
*   `/portfolio/province/<int:province_pk>/cover-page/` &rarr; `portfolio-province-cover-page`
*   `/portfolio/province/<int:province_pk>/cover-page/xlsx/` &rarr; `portfolio-province-cover-page-xlsx`
*   `/portfolio/province/<int:province_pk>/valuation-summary/` &rarr; `portfolio-province-valuation-summary`
*   `/portfolio/province/<int:province_pk>/valuation-summary/xlsx/` &rarr; `portfolio-province-valuation-summary-xlsx`

### 3. View Logic (`app/Project/views/portfolio_views.py`)

#### `PortfolioProvinceSummaryView`
*   Lists all provinces.
*   For each province, calculates:
    *   Number of active projects.
    *   Number of active projects with approved payment certificates.
    *   Total original contract value of those projects.
    *   Total cumulative certified amount from their latest approved certificates.

#### `ProvinceCoverPageView` & `ProvinceCoverPageDownloadXLSXView`
*   Aggregates progressive data (previous work done, current claim, materials, retention, advance payment, etc.) from the latest approved certificate of each active project in the province.
*   Constructs standard Section A, B, and C fields:
    *   Section A: Province Name, Project Count, Approved Certificate Count.
    *   Section B: Original Contract Value, approved variations, revised contract value, VAT, and total contract value.
    *   Section C: Work progressive previous, progressive current, progressive to date, retention, materials, advance payments, vat, and net amount due.

#### `ProvinceValuationSummaryView` & `ProvinceValuationSummaryDownloadXLSXView`
*   Renders a valuation summary table where each project in the province is a row.
*   Aggregates contract and progressive certified values per project.
*   Displays totals row at the bottom of the table.

### 4. Excel Exporters (`app/BillOfQuantities/exporters/`)
*   `export_province_cover_page_to_xlsx(province, projects)`: Aggregates values and writes to openpyxl sheet matching `01_Front.xlsx` styling.
*   `export_province_summary_report_to_xlsx(province, projects)`: Lists projects as rows, summing columns at the bottom, matching `02_Summary.xlsx` styling.

## Verification Plan

### Automated Tests
*   Create unit tests in `app/Project/tests/test_province_reports.py` checking view responses, aggregation calculations, and XLSX generation.
