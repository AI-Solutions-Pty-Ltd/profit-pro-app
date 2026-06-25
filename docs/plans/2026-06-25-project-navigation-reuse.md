# Reusable Project Configuration Navigation Tabs Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Refactor the WBS levels, disciplines, drawing types, and construction milestones navigation tabs to be reusable, unified, and integrated across all four configuration pages.

**Architecture:** Create a new Django include template `setup_nav.html` in `app/Project/templates/project/includes/` which accepts `project` and `active_tab`. Update all four views/templates to include this file.

**Tech Stack:** Django Templates, Tailwind CSS, Heroicons

---

### Task 1: Create reusable include template

**Files:**
- Create: [setup_nav.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/includes/setup_nav.html)

**Step 1: Write setup_nav.html**
Write the code content for `setup_nav.html` to define the 4 tabs with dynamic active tab styling and clean consistent classes.

**Step 2: Verify file existence**
Check that the file was created successfully.

**Step 3: Commit**
```bash
git add app/Project/templates/project/includes/setup_nav.html
git commit -m "feat: create reusable setup navigation template include"
```

---

### Task 2: Modify category_manage.html (WBS Levels)

**Files:**
- Modify: [category_manage.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/categories/category_manage.html)

**Step 1: Replace inline tabs with include**
Replace the inline tabs code with:
```html
{% include "project/includes/setup_nav.html" with project=project active_tab="wbs" %}
```

**Step 2: Commit**
```bash
git add app/Project/templates/project/categories/category_manage.html
git commit -m "refactor: use reusable navigation include in category_manage.html"
```

---

### Task 3: Modify discipline_manage.html

**Files:**
- Modify: [discipline_manage.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/disciplines/discipline_manage.html)

**Step 1: Replace inline tabs with include**
Replace the inline tabs code with:
```html
{% include "project/includes/setup_nav.html" with project=project active_tab="disciplines" %}
```

**Step 2: Commit**
```bash
git add app/Project/templates/project/disciplines/discipline_manage.html
git commit -m "refactor: use reusable navigation include in discipline_manage.html"
```

---

### Task 4: Modify drawing_type_manage.html

**Files:**
- Modify: [drawing_type_manage.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/drawing_types/drawing_type_manage.html)

**Step 1: Insert navigation include after header**
Insert the template include after the header section:
```html
{% include "project/includes/setup_nav.html" with project=project active_tab="drawing_types" %}
```

**Step 2: Commit**
```bash
git add app/Project/templates/project/drawing_types/drawing_type_manage.html
git commit -m "refactor: add reusable navigation include to drawing_type_manage.html"
```

---

### Task 5: Modify milestone_manage.html

**Files:**
- Modify: [milestone_manage.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/milestones/milestone_manage.html)

**Step 1: Insert navigation include after header**
Insert the template include after the header section:
```html
{% include "project/includes/setup_nav.html" with project=project active_tab="milestones" %}
```

**Step 2: Commit**
```bash
git add app/Project/templates/project/milestones/milestone_manage.html
git commit -m "refactor: add reusable navigation include to milestone_manage.html"
```

---

### Task 6: Add automated rendering tests

**Files:**
- Create: [test_navigation_tabs.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_navigation_tabs.py)

**Step 1: Write integration tests**
Write tests for the four pages verifying they render successfully (status 200) and contain the tab links/texts.

**Step 2: Run tests**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_navigation_tabs.py -v`
Expected: All tests pass.

**Step 3: Commit**
```bash
git add app/Project/tests/test_navigation_tabs.py
git commit -m "test: add rendering tests for project configuration navigation tabs"
```

---

### Task 7: Run verification checks

**Step 1: Run all Project tests**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/ -v`
Expected: All tests pass.

**Step 2: Check linting**
Run: `.venv\Scripts\python.exe -m ruff check app/Project`
Expected: No linting issues found.
