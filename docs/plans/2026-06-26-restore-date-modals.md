# Restore Date Modals Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Restore and wire up the dedicated date-editing modals on the Scope Planning page (scope_planning.html) for WBS Category, SubCategory, and Group levels, replacing the regular edit modals.

**Architecture:** Include category_scope_date_edit.html, subcategory_scope_date_edit.html, and group_scope_date_edit.html modal templates in scope_planning.html instead of the regular edit modals. Change the WBS Level card pencil buttons to invoke these date-only modals, populating start and end dates formatted with Django's Y-m-d date filter.

**Tech Stack:** Django Templates, TailwindCSS, Vanilla JS, Pytest

---

### Task 1: Update Modal Includes in scope_planning.html

**Files:**
- Modify: `app/Planning/templates/planning/scope_planning.html:9-20`

**Step 1: Replace category, subcategory, and group edit modals with date edit modals**

Modify `app/Planning/templates/planning/scope_planning.html` to replace the inclusion of:
- `project/categories/category_edit.html` -> `project/categories/category_scope_date_edit.html`
- `project/sub_categories/subcategory_edit.html` -> `project/sub_categories/subcategory_scope_date_edit.html`
- `project/groups/group_edit.html` -> `project/groups/group_scope_date_edit.html`

**Step 2: Commit**

```bash
git add app/Planning/templates/planning/scope_planning.html
git commit -m "feat: include scope planning date modals"
```

---

### Task 2: Update WBS Level Card Pencil Buttons in scope_planning.html

**Files:**
- Modify: `app/Planning/templates/planning/scope_planning.html`

**Step 1: Update L1 Category Pencil Button**

Modify the pencil button for categories (`category`) to trigger `openScopeCategoryDateModal`:
```html
<button type="button"
        onclick="openScopeCategoryDateModal({{ category.pk }}, '{{ category.name|escapejs }}', '{{ category.start_date|date:"Y-m-d" }}', '{{ category.end_date|date:"Y-m-d" }}')"
        class="p-2 text-indigo-600 rounded-lg transition-colors hover:bg-indigo-50"
        title="Edit category">{% heroicon_outline "pencil" size="18" %}</button>
```

**Step 2: Update L2 SubCategory Pencil Button**

Modify the pencil button for subcategories (`subcategory`) to trigger `openScopeSubCategoryDateModal`:
```html
<button type="button"
        onclick="openScopeSubCategoryDateModal({{ subcategory.pk }}, '{{ subcategory.name|escapejs }}', {{ category.pk }}, '{{ subcategory.start_date|date:"Y-m-d" }}', '{{ subcategory.end_date|date:"Y-m-d" }}')"
        class="p-1.5 text-indigo-600 rounded-lg transition-colors hover:bg-indigo-50"
        title="Edit subcategory">
    {% heroicon_outline "pencil" size="16" %}
</button>
```

**Step 3: Update L3 Group Pencil Button**

Modify the pencil button for groups (`group`) to trigger `openScopeGroupDateModal`:
```html
<button type="button"
        onclick="openScopeGroupDateModal({{ group.pk }}, '{{ group.name|escapejs }}', {{ subcategory.pk }}, '{{ group.start_date|date:"Y-m-d" }}', '{{ group.end_date|date:"Y-m-d" }}')"
        class="p-1.5 text-indigo-600 rounded-lg transition-colors hover:bg-indigo-50"
        title="Edit group">
    {% heroicon_outline "pencil" size="16" %}
</button>
```

**Step 4: Verify with pytest**

Run: `.venv\Scripts\python.exe -m pytest app/Planning/tests/test_scope_planning.py`
Expected: 11 passed

**Step 5: Commit**

```bash
git add app/Planning/templates/planning/scope_planning.html
git commit -m "feat: wire up pencil buttons to trigger scope date-editing modals"
```
