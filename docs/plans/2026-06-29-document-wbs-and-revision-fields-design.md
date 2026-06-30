# Design: Document WBS Level & Revision Fields

## Goal
The goal is to add `document_number`, `revision_number`, and full WBS level (Category L1, SubCategory L2, Group L3) selection capability to the `ProjectDocument` model, forms, and views to match the functionality of drawings.

---

## Proposed Changes

### 1. Database Model Changes
Modify [document_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/documents/document_models.py):
- Add `document_number` (`models.CharField`, blank=True)
- Add `revision_number` (`models.CharField`, blank=True)
- Add `sub_category` (`models.ForeignKey` to `SubCategory`, null=True, blank=True)
- Add `group` (`models.ForeignKey` to `Group`, null=True, blank=True)

### 2. Form Changes
Modify [document_forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/documents/document_forms.py):
- Add custom choice field `wbs_level`
- Populate `wbs_level` choices with all Level 1 (Category), Level 2 (SubCategory), and Level 3 (Group) entities filtered by project.
- In `save()`, parse and set the corresponding WBS relationships on the model instance.

### 3. Template Layout Changes
Modify [document_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/documents/document_form.html):
- Add `document_number` and `revision_number` to Left column.
- Add `wbs_level` to Right column.

---

## Verification Plan

### Database Migrations
Run the standard Django migration sequence:
```bash
.venv\Scripts\python.exe manage.py makemigrations
.venv\Scripts\python.exe manage.py migrate
```

### Automated Tests
Add test cases in `test_document_views.py` testing:
- Form WBS level resolution (submitting category, subcategory, group choices and checking they map correctly on the database record).
- Saving `document_number` and `revision_number`.
Run:
```bash
.venv\Scripts\python.exe -m pytest app/Project/tests/test_document_views.py -v
```
