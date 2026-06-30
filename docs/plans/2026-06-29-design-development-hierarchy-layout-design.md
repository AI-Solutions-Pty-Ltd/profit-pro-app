# Design: Design Development Hierarchy Layout

## Goal
The goal is to modify the Design Development overview layout in [design_development.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/overview/design_development.html) to use the card-based hierarchy layout from [budget_forecast.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/budget_forecast.html) and [scope_planning.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/scope_planning.html).

---

## Proposed Changes

### 1. Remove Tree Connector Lines
- Remove references to `{% include "components/tree_connector.html" ... %}`.
- Remove absolute/relative positioning styling elements used for the tree layout.

### 2. Implement Card-Based Hierarchy Layout
We will apply nested cards with specific border colors:
- **Level 1 (Category)**:
  - Left border color: `border-l-4 border-indigo-400`
  - Icon: `rectangle-stack`
  - Right side actions:
    - Sub-items pill: `{{ category.subcategories.count }} sub-items`
    - Add item button: `+ Add L1 Item` (styled as a modern indigo badge/button)
    - Collapse/expand toggle chevron
  - Expanded content container: Contains L1 category design items table followed by the L2 subcategories container.
  
- **Level 2 (Subcategory)**:
  - Left border color: `border-l-4 border-green-400`
  - Icon: `tag`
  - Right side actions:
    - Sub-items pill: `{{ subcategory.groups.count }} sub-items`
    - Add item button: `+ Add L2 Item` (styled as a modern green badge/button)
    - Collapse/expand toggle chevron
  - Expanded content container: Contains L2 subcategory design items table followed by the L3 groups container.

- **Level 3 (Group)**:
  - Left border color: `border-l-4 border-purple-400`
  - Icon: `folder`
  - Right side actions:
    - Add item button: `+ Add L3 Item` (styled as a modern purple badge/button)
    - Collapse/expand toggle chevron
  - Expanded content container: Contains L3 group design items table.

### 3. Handle Empty Sub-Levels (Fixing test failure)
- If a category has no subcategories, render:
  `No subcategories found for this category`
- If a subcategory has no groups, render:
  `No groups found for this subcategory`
- If a project has no categories, render:
  `No categories found` (matching the look of `budget_forecast.html` empty state)

---

## Verification Plan

### Automated Tests
Run the planning tests to verify the UI rendering assertions pass correctly:
```bash
.venv\Scripts\python.exe -m pytest app/Planning/tests/test_design_development.py -v
```
