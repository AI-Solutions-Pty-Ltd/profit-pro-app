# Portfolio Province Reports Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Create functionality to group active projects by province, showing summary stats and allowing users to view and download/export Cover Page and Valuation Summary reports aggregated by province.

**Architecture:** We will add a new tab "Province Summary" to the portfolio dashboard nav. Clicking it will display a table of provinces. For each province, users can view HTML pages or download Excel sheets of the aggregated Cover Page and Valuation Summary.

**Tech Stack:** Django, Python, HTML/Tailwind CSS, openpyxl for Excel generation, pytest for testing.

---

### Task 1: Navigation Tab Integration

**Files:**
- Modify: `app/Project/templates/portfolio/reports_nav.html`

**Step 1: Add new tab**
Add a navigation link for the Province Summary tab.
```html
<a href="{% url 'project:portfolio-province-summary' %}"
   class="border-b-2 {% if tab == 'province_summary' %}border-indigo-500 text-indigo-600{% else %}border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300{% endif %} py-4 px-1 text-sm font-medium transition-colors">
    Province Summary
</a>
```

**Step 2: Commit**
```bash
git add app/Project/templates/portfolio/reports_nav.html
git commit -m "feat: add Province Summary tab to navigation header"
```

---

### Task 2: URL Routing for Province Reports

**Files:**
- Modify: `app/Project/urls/portfolio_urls.py`

**Step 1: Add new URL paths**
```python
    path(
        "reports/province/",
        portfolio_views.PortfolioProvinceSummaryView.as_view(),
        name="portfolio-province-summary",
    ),
    path(
        "province/<int:province_pk>/cover-page/",
        portfolio_views.ProvinceCoverPageView.as_view(),
        name="portfolio-province-cover-page",
    ),
    path(
        "province/<int:province_pk>/cover-page/xlsx/",
        portfolio_views.ProvinceCoverPageDownloadXLSXView.as_view(),
        name="portfolio-province-cover-page-xlsx",
    ),
    path(
        "province/<int:province_pk>/valuation-summary/",
        portfolio_views.ProvinceValuationSummaryView.as_view(),
        name="portfolio-province-valuation-summary",
    ),
    path(
        "province/<int:province_pk>/valuation-summary/xlsx/",
        portfolio_views.ProvinceValuationSummaryDownloadXLSXView.as_view(),
        name="portfolio-province-valuation-summary-xlsx",
    ),
```

**Step 2: Commit**
```bash
git add app/Project/urls/portfolio_urls.py
git commit -m "feat: define URL routes for province summary and reports"
```

---

### Task 3: Exporters for Aggregated Province Reports

**Files:**
- Create: `app/BillOfQuantities/exporters/province_cover_page_exporter.py`
- Create: `app/BillOfQuantities/exporters/province_summary_report_exporter.py`

**Step 1: Create Province Cover Page Exporter**
```python
import datetime
from decimal import Decimal
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from app.BillOfQuantities.views.payment_certificate_views import get_resolved_cover_page_sections

def export_province_cover_page_to_xlsx(province, projects):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Province Cover Page"
    
    # Mirror style and headers from single cover page
    font_bold = Font(bold=True)
    font_title = Font(bold=True, size=14)
    align_center = Alignment(horizontal="center", vertical="center")
    
    ws.cell(row=1, column=1, value="[ LOGO ]").font = font_bold
    ws.cell(row=1, column=1).alignment = align_center
    
    title_cell = ws.cell(row=1, column=3, value=f"PROVINCE COVER PAGE — {province.name.upper()}")
    title_cell.font = font_title
    title_cell.alignment = align_center
    ws.merge_cells(start_row=1, start_column=3, end_row=1, end_column=6)
    
    # Rest of the sheet formatting is filled in with the aggregated sections
    return wb
```

**Step 2: Create Province Valuation Summary Exporter**
```python
from decimal import Decimal
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

def export_province_valuation_summary_to_xlsx(province, projects_data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Province Valuation Summary"
    
    # Headers
    headers = [
        "PROJECT NAME", "STATUS", "TENDER AMOUNT (R)", "REVISED CONTRACT VALUE (R)",
        "PREVIOUS CERTIFIED (R)", "PROGRESSIVE TO DATE (R)", "NET CLAIMED (R)", "FORECAST AT COMPLETION (R)"
    ]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        
    # Write project rows and totals row
    return wb
```

**Step 3: Commit**
```bash
git add app/BillOfQuantities/exporters/province_cover_page_exporter.py app/BillOfQuantities/exporters/province_summary_report_exporter.py
git commit -m "feat: implement skeleton exporters for province XLSX downloads"
```

---

### Task 4: View Classes in `portfolio_views.py`

**Files:**
- Modify: `app/Project/views/portfolio_views.py`

**Step 1: Write View Classes**
Define `PortfolioProvinceSummaryView`, `ProvinceCoverPageView`, `ProvinceValuationSummaryView`, and XLSX download views. Make sure they use `SubscriptionRequiredMixin` and check access to projects.

**Step 2: Commit**
```bash
git add app/Project/views/portfolio_views.py
git commit -m "feat: implement View classes for province summary, coverpage, and valuation summary"
```

---

### Task 5: Templates for HTML View

**Files:**
- Create: `app/Project/templates/portfolio/reports/province_summary.html`
- Create: `app/Project/templates/portfolio/reports/province_cover_page.html`
- Create: `app/Project/templates/portfolio/reports/province_valuation_summary.html`

**Step 1: Implement HTML Templates**
Ensure premium aesthetics (vibrant headers, crisp borders, clean typography, hover animations) using Tailwind CSS.

**Step 2: Commit**
```bash
git add app/Project/templates/portfolio/reports/province_summary.html app/Project/templates/portfolio/reports/province_cover_page.html app/Project/templates/portfolio/reports/province_valuation_summary.html
git commit -m "feat: create template screens for province reports"
```

---

### Task 6: Unit Tests and Verification

**Files:**
- Create: `app/Project/tests/test_province_reports.py`

**Step 1: Implement unit tests**
Write pytest test cases utilizing `ProvinceFactory`, `ProjectFactory`, and `PaymentCertificateFactory` from Factories. Test the view status codes, aggregation calculations, and XLSX downloads.

**Step 2: Verify and Commit**
```bash
pytest app/Project/tests/test_province_reports.py
git add app/Project/tests/test_province_reports.py
git commit -m "test: add unit tests for province reports feature"
```
