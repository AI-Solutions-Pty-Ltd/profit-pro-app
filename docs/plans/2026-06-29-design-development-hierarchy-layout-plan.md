# Design Development Hierarchy Layout Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Refactor [design_development.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/overview/design_development.html) to use the card-based hierarchy layout from [budget_forecast.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/budget_forecast.html).

**Architecture:** We will replace the tree connector layout in the template with fully nested collapsible cards (L1, L2, L3) using colors and structures that match the other planning views, and add empty state messages to pass the existing test suite.

**Tech Stack:** Django Template Engine, HTML, Tailwind CSS, Heroicons.

---

### Task 1: Refactor design_development.html Category (L1) Level

**Files:**
- Modify: [design_development.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/overview/design_development.html)

**Step 1: Replace Category list section**
Update the loop for `project.categories.all` to structure L1 categories as card components with an indigo-400 left border, sub-items count pill, "+ Add L1 Item" button, and chevron toggle.

**Step 2: Verify test output**
Run: `.venv\Scripts\python.exe -m pytest app/Planning/tests/test_design_development.py -v`
Expected: Fails only on empty subcategory message since L2/L3 are not yet updated.

**Step 3: Commit changes**
```bash
git add app/Planning/templates/planning/overview/design_development.html
git commit -m "style: refactor L1 categories to card hierarchy layout"
```

---

### Task 2: Refactor design_development.html Subcategory (L2) Level

**Files:**
- Modify: [design_development.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/overview/design_development.html)

**Step 1: Replace Subcategory list section**
Update the nested subcategories loop to render L2 subcategories as card components with a green-400 left border, sub-items count pill, "+ Add L2 Item" button, chevron toggle, and display the message `"No subcategories found for this category"` if empty.

**Step 2: Verify test output**
Run: `.venv\Scripts\python.exe -m pytest app/Planning/tests/test_design_development.py -v`
Expected: Passes! (The empty subcategory test passes now).

**Step 3: Commit changes**
```bash
git add app/Planning/templates/planning/overview/design_development.html
git commit -m "style: refactor L2 subcategories to card hierarchy layout and add empty message"
```

---

### Task 3: Refactor design_development.html Group (L3) Level

**Files:**
- Modify: [design_development.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/overview/design_development.html)

**Step 1: Replace Group list section**
Update the nested groups loop to render L3 groups as card components with a purple-400 left border, "+ Add L3 Item" button, chevron toggle, and display the message `"No groups found for this subcategory"` if empty.

**Step 2: Run verification**
Run: `.venv\Scripts\python.exe -m pytest app/Planning/tests/test_design_development.py -v`
Expected: All tests pass.

**Step 3: Commit changes**
```bash
git add app/Planning/templates/planning/overview/design_development.html
git commit -m "style: refactor L3 groups to card hierarchy layout"
```
