# Portfolio Dashboard Filters Refactoring Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Add name search, province, and municipality filters to the Portfolio Dashboard, refactoring the layout to look clean, user-friendly, and consistent with the Project List page filters.

**Architecture:** Modify `portfolio_dashboard.html` to update the form structure, remove inline reloads, add the advanced filters drawer and active badges, and add Javascript for state toggling and dynamic municipality filtering.

**Tech Stack:** Django Templates, Tailwind CSS, Javascript

---

### Task 1: Update the filter form in portfolio_dashboard.html

**Files:**
- Modify: [portfolio_dashboard.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/portfolio/portfolio_dashboard.html)

**Step 1: Replace filter form**
Replace the existing inline filters form in `portfolio_dashboard.html` with a modern collapsible form (search, advanced toggle, apply, clear, and collapsible advanced drawer).

**Step 2: Commit**
```bash
git add app/Project/templates/portfolio/portfolio_dashboard.html
git commit -m "feat: refactor filter form and add advanced drawer in portfolio_dashboard.html"
```

---

### Task 2: Add Javascript logic to portfolio_dashboard.html

**Files:**
- Modify: [portfolio_dashboard.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/portfolio/portfolio_dashboard.html)

**Step 1: Append JS code**
Add event listeners to toggle the advanced filters drawer and perform client-side dynamic municipality filtering based on selected province.

**Step 2: Commit**
```bash
git add app/Project/templates/portfolio/portfolio_dashboard.html
git commit -m "feat: add filters toggle and dynamic municipality JS to portfolio_dashboard.html"
```

---

### Task 3: Add automated tests for portfolio dashboard filters

**Files:**
- Create: [test_portfolio_filters.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_portfolio_filters.py)

**Step 1: Write filter tests**
Write unit tests verifying `PortfolioDashboardView` handles filtering by name search, province, and municipality, returning correct subsets of projects.

**Step 2: Run tests**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_portfolio_filters.py -v`
Expected: PASS

**Step 3: Commit**
```bash
git add app/Project/tests/test_portfolio_filters.py
git commit -m "test: add unit tests for portfolio dashboard filters"
```

---

### Task 4: Run verification checks

**Step 1: Run all Project tests**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/ -v`
Expected: All tests pass.

**Step 2: Check linting**
Run: `.venv\Scripts\python.exe -m ruff check app/Project`
Expected: No linting issues found.
