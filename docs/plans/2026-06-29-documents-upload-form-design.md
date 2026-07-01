# Design: Documents Upload Form Refactoring

## Goal
The goal is to refactor [document_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/documents/document_form.html) to match the 2-column hierarchy layout of [drawing_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/documents/drawing_form.html).

---

## Proposed Changes

### 1. Structure Template Layout
We will update [document_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/documents/document_form.html) to implement the grid layout structure:
- **Identification (Left Column)**:
  - Document Title (`title`)
  - Document Category (`category`), visible only when viewing/editing the `"OTHER"` category.
- **Classification & Hierarchy (Right Column)**:
  - Discipline (`project_discipline`)
  - Sector (`project_category`), visible only when category is not a drawing/specification view.
  - Area (`area`), visible only when category is not a drawing/specification view.
- **File & Notes (Bottom Section)**:
  - Current File info wrapper (on edit view).
  - File upload (`file`)
  - Additional Notes (`notes`)

### 2. Actions and Buttons
- Styled footer layout matching the buttons and spacing in the drawings form card.
- Retain the exact icons, classes, and `loading-btn` properties (`data-loading-text`, `data-disable-elements`) to ensure correct client-side loading actions.

---

## Verification Plan

### Automated Tests
We will add a new test file [test_document_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_document_views.py) containing integration tests for:
- Creating a document (DocumentCreateView)
- Updating an existing document (DocumentEditView)
- Verifying correct layout fields are rendered.

Run the tests using:
```bash
.venv\Scripts\python.exe -m pytest app/Project/tests/test_document_views.py -v
```
