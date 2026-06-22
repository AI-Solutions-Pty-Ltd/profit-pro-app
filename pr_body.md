## Summary
- Removed drawing self-hierarchy `parent` field and added `group` (WBS L3) field to the `Drawing` model.
- Refactored `DrawingForm` to include a single hierarchical `wbs_level` field alongside the model's `category` field.
- Implemented automatic parent WBS level resolution on form save: selecting a Group or SubCategory automatically determines and saves the correct parent levels (category, sub_category) in the database.
- Redesigned `drawing_form.html` template to render `category` and `wbs_level` cleanly.
- Updated `drawing_list.html` to render structured WBS Level badges (L1, L2, L3) and removed drawing parent details.
- Added thorough model, form, and validation tests in `test_drawings.py` (all passing).

## Test Plan
- Run tests: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_drawings.py -v`
- Confirm all migrations apply cleanly: `.venv\Scripts\python.exe manage.py migrate`
