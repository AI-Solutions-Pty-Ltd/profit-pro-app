# Design Document: Collapsible Category-Subcategory-Group Hierarchy

This document outlines the design for updating the category management view (`category_manage.html`) to display a nested, tree-like hierarchy of Categories (Level 1), Subcategories (Level 2), and Groups (Level 3), complete with a collapse/expand feature and direct inline actions for all levels.

## Goals

1. **Collapsible Hierarchy**: Display a project's categories (L1), subcategories (L2), and groups (L3) nested within each other rather than in a flat list or on separate pages.
2. **Expand/Collapse Interaction**: Implement visual toggles (chevrons) for expanding and collapsing levels on the client side, reusing `toggle-utils.js`.
3. **Inline CRUD Actions**: Allow users to create, edit, and delete L1, L2, and L3 entries from the single category management dashboard using existing modals.
4. **Visual Consistency**: Match the clean, card-based look and color schemes from the Scope Planning Work Breakdown Structure (WBS).

## Proposed Changes

### 1. View & Context Update

#### [MODIFY] [category_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/category_views.py)
Update `CategoryListView.get_context_data` to inject `subcategory_form` and `group_form` into the page context. This is required so the inline modals can render properly.

```python
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["category_form"] = CategoryForm()
        context["subcategory_form"] = SubCategoryForm(project=project)
        context["group_form"] = GroupForm(project=project)
        return context
```

### 2. Template Refactor

#### [MODIFY] [category_manage.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/categories/category_manage.html)
- Replace the current flat `<table>` representation of categories with a nested card list similar to `scope_planning.html`.
- **Level 1 (Category)**: Blue border/background cards.
  - Toggles `category-{{ category.pk }}`.
  - Shows name and description.
  - Buttons: Add Level 2, Edit, Delete, Toggle.
- **Level 2 (Subcategory)**: Nested green border/background cards under Level 1.
  - Toggles `subcategory-{{ subcategory.pk }}`.
  - Shows name and description.
  - Buttons: Add Level 3, Edit, Delete, Toggle.
- **Level 3 (Group)**: Nested purple border/background cards under Level 2.
  - Shows name and description.
  - Buttons: Edit, Delete.
- Include the following modal partials at the top of the file:
  - Subcategory: `subcategory_create.html`, `subcategory_edit.html`, `subcategory_delete.html`
  - Group: `group_create.html`, `group_edit.html`, `group_delete.html`
- Load `toggle-utils.js` script inside the `extra_js` block.

## Verification Plan

### Automated Tests
- We will execute the existing suite of project tests using pytest to verify that we haven't introduced any regression to categories, subcategories, or groups.
```bash
.venv\Scripts\python.exe -m pytest app/Project/tests/ -v
```

### Manual Verification
- Verify that expanding and collapsing L1 and L2 cards works smoothly.
- Test inline operations (Add/Edit/Delete) for Categories, Subcategories, and Groups:
  - Verify Category CRUD operates correctly and updates the view.
  - Verify Subcategory CRUD operates correctly and updates the nested view.
  - Verify Group CRUD operates correctly and updates the nested view.
