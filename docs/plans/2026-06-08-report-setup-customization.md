# Report Selection and Configuration Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Implement report selection (Standard vs. Lephadimisha BOQ layout), layout preview, custom column reordering/renaming/visibility in Project Setup, and integrate this into a simplified 2-card download interface in Payment Certificate detail view.

**Architecture:** 
- Extend `Project` model with a `column_config` JSONField and add `LEPHADIMISHA` choice to `CertificateLayout`.
- Add custom view logic and form fields to capture report configuration and serve live previews.
- Refactor PDF templates and Excel exporters to render dynamically based on `column_config` and active layouts.
- Re-work the payment certificate detail UI to display 2 download cards (Full and Abridged) with embedded page selectors and dual download buttons.

**Tech Stack:** Python 3.13+, Django, TailwindCSS, Vanilla JavaScript (for interactive setup/preview), openpyxl (Excel), PyPDF (PDF compilation).

---

### Task 1: Extend Project Model and Create Migration

**Files:**
- Modify: `app/Project/projects/projects_models.py`
- Test: `app/Project/tests/test_models.py`

**Step 1: Write the failing test**
In `app/Project/tests/test_models.py`:
```python
def test_project_has_report_configuration(self):
    from app.Project.tests.factories import ProjectFactory
    project = ProjectFactory.create(certificate_layout="LEPHADIMISHA")
    assert project.certificate_layout == "LEPHADIMISHA"
    assert hasattr(project, "column_config")
    assert isinstance(project.column_config, dict)
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_models.py -k test_project_has_report_configuration`
Expected: FAIL with attribute error / value validation error.

**Step 3: Write minimal implementation**
In `app/Project/projects/projects_models.py`:
Add `LEPHADIMISHA = "LEPHADIMISHA", "Lephadimisha BOQ Report"` to `CertificateLayout` choices.
Add the field `column_config = models.JSONField(default=dict, blank=True)` to `Project` model.
Define `get_column_config(self)` helper to return the list of column settings merged with defaults.

Run command to create migrations:
`.venv\Scripts\python.exe manage.py makemigrations`
`.venv\Scripts\python.exe manage.py migrate`

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_models.py -k test_project_has_report_configuration`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Project/projects/projects_models.py app/Project/tests/test_models.py app/Project/migrations/*
git commit -m "feat: add report layout and column config to Project model"
```

---

### Task 2: Build Report Configuration Form and Setup UI

**Files:**
- Modify: `app/Project/projects/project_forms.py`
- Modify: `app/Project/projects/project_views.py`
- Modify: `app/Project/templates/project/project_setup.html`

**Step 1: Write the failing test**
In `app/Project/tests/test_views.py` (or project views tests):
```python
def test_project_setup_view_includes_layout_config(self):
    from app.Project.tests.factories import ProjectFactory
    from django.urls import reverse
    project = ProjectFactory.create()
    url = reverse("project:project-setup", kwargs={"pk": project.pk})
    # check that form/view handles setup submission
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -k test_project_setup_view_includes_layout_config`
Expected: FAIL

**Step 3: Write minimal implementation**
- Update `ProjectForm` or create `ReportConfigForm` to validate and save `certificate_layout` and `column_config`.
- Add a beautiful Tailwind-styled card "Report Selection & Configuration" in `project_setup.html`.
- Add interactive list items (reorder, rename, show/hide) and a live mock preview table that updates dynamically via JavaScript.
- Save config when form is submitted.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -k test_project_setup_view_includes_layout_config`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Project/projects/project_forms.py app/Project/projects/project_views.py app/Project/templates/project/project_setup.html
git commit -m "feat: add report selection and column config form and UI in project setup"
```

---

### Task 3: Implement Dynamic Column Configuration in PDF Generation

**Files:**
- Modify: `app/BillOfQuantities/tasks.py`
- Modify: `app/BillOfQuantities/templates/pdf_templates/line_items_table.html`
- Create/Modify templates under `valterra_rpm/` as needed to support dynamic columns.

**Step 1: Write the failing test**
In `app/BillOfQuantities/tests/test_exporters.py`:
```python
def test_compile_pdf_with_custom_columns(self):
    from app.Project.tests.factories import ProjectFactory
    from app.BillOfQuantities.tests.factories import PaymentCertificateFactory
    # Configure custom column visibility
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf_with_custom_columns`
Expected: FAIL

**Step 3: Write minimal implementation**
- Modify `compile_pdf_for_certificate` in `tasks.py` to retrieve `column_config` from the project.
- Modify `line_items_table.html` and Valterra templates to dynamically loop over active/enabled columns in the correct order using the custom labels.
- Adjust PDF layout styling to ensure dynamic columns render properly without overlapping.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_compile_pdf_with_custom_columns`
Expected: PASS

**Step 5: Commit**
```bash
git add app/BillOfQuantities/tasks.py app/BillOfQuantities/templates/pdf_templates/*
git commit -m "feat: render PDF tables dynamically based on custom column config"
```

---

### Task 4: Implement Dynamic Column Configuration in Excel Generation

**Files:**
- Modify: `app/BillOfQuantities/exporters/excel_exporter.py`
- Test: `app/BillOfQuantities/tests/test_exporters.py`

**Step 1: Write the failing test**
In `app/BillOfQuantities/tests/test_exporters.py`:
```python
def test_excel_exporter_with_custom_columns(self):
    # Test dynamic column generation and formula verification
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_excel_exporter_with_custom_columns`
Expected: FAIL

**Step 3: Write minimal implementation**
- Update `generate_payment_certificate_excel` to resolve active columns dynamically.
- Compute column cell letters (e.g. A, B, C, etc.) based on their current active order.
- Dynamically write header cells and data cells.
- Calculate formula strings (like `=E{row}*F{row}`) using resolved cell letters.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_excel_exporter_with_custom_columns`
Expected: PASS

**Step 5: Commit**
```bash
git add app/BillOfQuantities/exporters/excel_exporter.py
git commit -m "feat: generate Excel sheets dynamically according to column config"
```

---

### Task 5: Refactor Download PDF Reports Interface

**Files:**
- Modify: `app/BillOfQuantities/templates/payment_certificate/payment_certificate_detail.html`
- Modify: `app/BillOfQuantities/views/payment_certificate_views.py`

**Step 1: Write the failing test**
In `app/BillOfQuantities/tests/test_exporters.py`:
```python
def test_payment_certificate_download_views(self):
    # Test download endpoints receive selected sections and correct layout
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_payment_certificate_download_views`
Expected: FAIL

**Step 3: Write minimal implementation**
- Modify `payment_certificate_detail.html` to show 2 cards instead of 4.
- In Card 1 (Full) and Card 2 (Abridged), add checkboxes for Cover Page, Valuation Summary, and Detailed Report, plus dual buttons for PDF and Excel.
- Connect forms to correct download views and update views to capture query parameters (`front`, `summary`, `detailed`, `format`) and serve either PDF or Excel.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_exporters.py -k test_payment_certificate_download_views`
Expected: PASS

**Step 5: Commit**
```bash
git add app/BillOfQuantities/templates/payment_certificate/payment_certificate_detail.html app/BillOfQuantities/views/payment_certificate_views.py
git commit -m "feat: refactor download UI to 2-card system with options and dual buttons"
```
