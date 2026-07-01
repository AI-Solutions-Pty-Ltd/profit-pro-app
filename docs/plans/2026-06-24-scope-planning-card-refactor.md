# Scope Planning Card Refactor — Design Doc

**Date:** 2026-06-24  
**Goal:** Add start/end date fields to WBS create/edit modals; refactor cards to show dates as formatted text; remove "Load Categories from other projects" feature.

---

## What Changes

### Card Layout (before → after)

**Before:** Each card had inline `<input type="date">` that triggered an API call on `change` + full page reload. Cluttered and hard to use.

**After:** Dates shown as clean formatted text on the card. Clicking the **edit ✏️** icon opens a modal that lets you edit name, description, start date, and end date all in one place.

```
[icon]  L1: Category Name          📅 Jun 1, 2026 → Jul 31, 2026    [3 milestones]  [✏️] [🗑️] [⬆️] [>]
[icon]  L1: Category Name          📅 No dates set                   [0 milestones]  [✏️] [🗑️] [⬆️] [>]
```

### Modal Fields (before → after)

**Before:** Create and edit modals only had `name` + `description`.  
**After:** All modals include `name`, `description`, `start_date`, `end_date`.

### Removed

- "Load Categories" button (loads WBS from another project)
- `loadCategoriesModal` HTML block
- `LoadWBSCategoriesView` class in `views.py`
- `load-categories` URL registration
- `other_projects` from `ScopePlanningView` context
- All inline `date_input.html` includes in `scope_planning.html`

---

## Files to Touch

| File | Change |
|---|---|
| `app/Project/projects/category_forms.py` | Add `start_date`, `end_date` to CategoryForm, SubCategoryForm, GroupForm |
| `app/Project/templates/project/categories/category_create.html` | Add date fields + pass to JS |
| `app/Project/templates/project/categories/category_edit.html` | Add date fields + populate in `openEditCategoryModal()` |
| `app/Project/templates/project/sub_categories/subcategory_create.html` | Add date fields |
| `app/Project/templates/project/sub_categories/subcategory_edit.html` | Add date fields + populate in `openEditSubCategoryModal()` |
| `app/Project/templates/project/groups/group_create.html` | Add date fields |
| `app/Project/templates/project/groups/group_edit.html` | Add date fields + populate in `openEditGroupModal()` |
| `app/Planning/templates/planning/scope_planning.html` | Remove Load Categories, remove date_input includes, show formatted dates, update edit modal call signatures |
| `app/Planning/views.py` | Remove `LoadWBSCategoriesView`, remove `other_projects` from context |
| `app/Planning/urls.py` | Remove `load-categories` URL |
