# Documents Upload Form Refactoring Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Refactor [document_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/documents/document_form.html) to match the layout of [drawing_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/documents/drawing_form.html).

**Architecture:** We will modify the HTML template to implement the 2-column split with crispy fields. We will also add a new unit test suite [test_document_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_document_views.py) to test creation and modification views.

**Tech Stack:** Django Template Engine, HTML, Tailwind CSS, pytest, factory_boy.

---

### Task 1: Create automated tests for Document views

**Files:**
- Create: [test_document_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_document_views.py)

**Step 1: Write test cases**
Write tests for creating a document, editing a document, and verifying correct status codes and contexts.

**Step 2: Run test suite to verify it works (or fails if it needs specific templates)**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_document_views.py -v`
Expected: PASS

**Step 3: Commit changes**
```bash
git add app/Project/tests/test_document_views.py
git commit -m "test: add integration tests for project document upload and edit views"
```

---

### Task 2: Refactor document_form.html template

**Files:**
- Modify: [document_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/documents/document_form.html)

**Step 1: Replace raw fields stack with card and grid columns**
Apply the 2-column layout for Identification and Classification fields, keep dynamic/hidden fields, file upload, cancel and save buttons.

**Step 2: Run test suite to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_document_views.py -v`
Expected: PASS

**Step 3: Commit changes**
```bash
git add app/Project/templates/documents/document_form.html
git commit -m "feat: refactor document upload form template to match drawings form layout"
```
