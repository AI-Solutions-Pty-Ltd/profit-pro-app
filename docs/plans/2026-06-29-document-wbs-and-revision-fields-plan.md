# Document WBS Level & Revision Fields Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Add `document_number`, `revision_number`, and WBS level (L1/L2/L3) selection capability to the `ProjectDocument` model, form, and templates.

**Architecture:** We will modify the model fields, generate database migrations, update the form field initialization and saving logic, update the template fields, and verify it with pytest.

**Tech Stack:** Django, SQLite/PostgreSQL, HTML, CSS, Tailwind CSS, pytest.

---

### Task 1: Update ProjectDocument model and generate migrations

**Files:**
- Modify: [document_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/documents/document_models.py)

**Step 1: Add new model fields**
Add `document_number`, `revision_number`, `sub_category`, and `group`.

**Step 2: Generate and apply migrations**
Run:
```bash
.venv\Scripts\python.exe manage.py makemigrations
.venv\Scripts\python.exe manage.py migrate
```

---

### Task 2: Refactor ProjectDocumentForm

**Files:**
- Modify: [document_forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/documents/document_forms.py)

**Step 1: Add WBS selection logic**
Add choice field `wbs_level` and widgets, labels, help texts, initial value parsing, and custom mapping save logic.

---

### Task 3: Update document_form.html layout

**Files:**
- Modify: [document_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/documents/document_form.html)

**Step 1: Place fields in grid**
Render `document_number`, `revision_number`, and `wbs_level` in their respective columns.

---

### Task 4: Add unit tests and run validations

**Files:**
- Modify: [test_document_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_document_views.py)

**Step 1: Author tests**
Add test cases checking that WBS level categories/subcategories/groups resolve correctly and number/revision fields save correctly.

**Step 2: Run test suite**
Run:
```bash
.venv\Scripts\python.exe -m pytest app/Project/tests/test_document_views.py -v
```
Expected: PASS
