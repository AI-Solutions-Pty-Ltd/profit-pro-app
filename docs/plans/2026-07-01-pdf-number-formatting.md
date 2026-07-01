# PDF Number Formatting Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Format all currency values in the aggregated Valuation Summary PDF report with space separation for thousands (e.g., R 10 185 098.35).

**Architecture:** Apply the `space_intcomma` filter from the custom Django tag library `template_extras` to all numbers in [valuation_summary_pdf.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/portfolio/reports/valuation_summary_pdf.html).

**Tech Stack:** Python 3.13+, Django, pytest-django

---

### Task 1: Add `space_intcomma` to all currency values in Valuation Summary PDF template

**Files:**
- Modify: [valuation_summary_pdf.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/portfolio/reports/valuation_summary_pdf.html)

**Step 1: Write a test asserting formatting changes**

Wait, let's write a unit test inside [test_project_groups.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_project_groups.py) that checks if the returned PDF or rendered HTML string contains formatted numbers like `R 120 000.00` instead of `R 120000.00`.
Actually, since PDF rendering is mocked or outputs raw binary bytes, we can write a test case rendering the template directly using Django's template rendering system to verify the formatted string output.

Let's write the test case:
```python
from django.template import Template, Context
def test_pdf_template_formatting():
    # Test rendering of a small template snippet using template_extras and space_intcomma
    t = Template("{% load template_extras %}{{ val|floatformat:2|space_intcomma }}")
    c = Context({"val": 120000.00})
    rendered = t.render(c)
    assert rendered == "120 000.00"
```

**Step 2: Run pytest to verify the new test passes** (since the filter already exists, this unit test will verify the filter works correctly)

Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_project_groups.py -k test_pdf_template_formatting -v`
Expected: PASS

**Step 3: Modify the PDF template to use `space_intcomma`**

Add `{% load template_extras %}` to the top of [valuation_summary_pdf.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/portfolio/reports/valuation_summary_pdf.html).
Update all currency values from `|floatformat:2` to `|floatformat:2|space_intcomma`.

**Step 4: Verify existing tests and PDF generation still pass**

Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_project_groups.py -v`
Expected: PASS

**Step 5: Commit changes**

```bash
git add app/Project/templates/portfolio/reports/valuation_summary_pdf.html app/Project/tests/test_project_groups.py
git commit -m "feat: format numbers with space_intcomma in valuation summary PDF report"
```
