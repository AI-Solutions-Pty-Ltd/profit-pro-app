# Design Doc: Restoring Scope Planning Date Modals

## Goal
Restore and wire up the dedicated date-editing modals on the Scope Planning page (`scope_planning.html`) for WBS Levels 1, 2, and 3, replacing the regular edit modals.

## Constraints
- The level names and descriptions must remain read-only when accessed from the Scope Planning page.
- Date fields (start_date, end_date) must be editable and updated via existing AJAX POST endpoints.
- Avoid bloating the HTML of `scope_planning.html` with unused name-editing modals for Categories, Subcategories, and Groups.

## Architecture & Components
We will use the existing date-editing modal components that are already implemented but currently unreferenced in `scope_planning.html`:
- `app/Project/templates/project/categories/category_scope_date_edit.html` (Modal ID: `scopeCategoryDateModal`)
- `app/Project/templates/project/sub_categories/subcategory_scope_date_edit.html` (Modal ID: `scopeSubCategoryDateModal`)
- `app/Project/templates/project/groups/group_scope_date_edit.html` (Modal ID: `scopeGroupDateModal`)

## Proposed Changes

### 1. `app/Planning/templates/planning/scope_planning.html`
- Replace regular edit modal includes for Category, SubCategory, and Group with their respective scope date edit modal templates.
- Update pencil button `onclick` handlers on WBS cards to trigger the corresponding scope date modal function, passing correctly formatted date parameters using Django's `|date:"Y-m-d"` filter.

## Verification
- Verify that clicking the pencil buttons correctly opens the date-only edit modals.
- Verify that saving new dates sends successful AJAX requests to the date update API endpoints and reloads the page with updated dates.
- Execute the test suite to ensure all unit tests pass:
  `.venv\Scripts\python.exe -m pytest app/Planning/tests/test_scope_planning.py`
