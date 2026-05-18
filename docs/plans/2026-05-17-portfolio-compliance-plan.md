# Portfolio Compliance Aggregation Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Update the Master Dashboard so that compliance metrics (RFIs, NCRs, Incidents) show project counts in portfolio view and exact item counts in single-project view.

**Architecture:** Use `projects.count() > 1` inside `MasterDashboardDataMixin` to toggle between `.values('project').distinct().count()` and `.count()`. Pass dynamic label `issue_type` to template.

**Tech Stack:** Django ORM, HTML Templates

---

### Task 1: Update Backend Context in `company_views.py`

**Files:**
- Modify: `c:/Users/nebst/Projects/profit-pro-app/app/Project/company/company_views.py`

**Step 1: Write the failing test**
*Skipped due to lack of explicit test scope.*

**Step 2: Run test to verify it fails**
N/A

**Step 3: Write minimal implementation**
Modify `_get_compliance_summary` in `MasterDashboardDataMixin` to conditionally use `.values("project").distinct().count()` and return `issue_type: "Projects"` if `projects.count() > 1`.

**Step 4: Run test to verify it passes**
N/A

**Step 5: Commit**
```bash
git add app/Project/company/company_views.py
git commit -m "feat: Context-aware compliance aggregation in MasterDashboardDataMixin"
```

---

### Task 2: Update UI Labels in `_summary_stats.html`

**Files:**
- Modify: `c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/company/partials/master_dashboard/_summary_stats.html`

**Step 1: Write the failing test**
N/A

**Step 2: Run test to verify it fails**
N/A

**Step 3: Write minimal implementation**
Update `Total Active Number` to use `{{ project_count|default:"0" }}`.
Update Cost/Schedule overrun descriptions to `{{ production.overrun_type }} with cost overruns`.
Update Correspondence/Safety/Quality descriptions to `{{ compliance.issue_type }} with pending matters`.

**Step 4: Run test to verify it passes**
N/A

**Step 5: Commit**
```bash
git add app/Project/templates/company/partials/master_dashboard/_summary_stats.html
git commit -m "ui: Dynamic text labels for portfolio vs project issue counts"
```
