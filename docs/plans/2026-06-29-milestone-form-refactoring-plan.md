# Milestone Form Refactoring Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Refactor the milestone form to remove WBS, Area, and Discipline start and end date fields, and cleanly present all five classification select fields (WBS Level 1, WBS Level 2, WBS Level 3, Area, Discipline) filtered by project.

**Architecture:** Update `MilestoneForm` in `milestone_forms.py` to remove date fields and add `project_sub_category`, query-filter it in `__init__`, and revise `milestone_form.html` to render the clean select fields in a grid.

**Tech Stack:** Python 3.11+, Django 5.2+, pytest, TailwindCSS.

---

### Task 1: Form Refactoring

**Files:**
- Modify: `app/Project/milestone_schedules/milestone_forms.py`
- Test: `app/Project/tests/test_milestones.py`

**Step 1: Write a test verifying MilestoneForm fields and queries**
Write a new test method in `app/Project/tests/test_milestones.py` to check that the form fields exclude the date fields and include `project_sub_category`, properly filtered by project.

```python
def test_milestone_form_fields_and_filtering(self):
    """Test that MilestoneForm contains only correct select fields and filters them by project."""
    from app.Project.milestone_schedules.milestone_forms import MilestoneForm
    from app.Project.tests.factories import ProjectFactory, CategoryFactory, SubCategoryFactory
    
    project = ProjectFactory()
    category1 = CategoryFactory(project=project, name="Cat A")
    category2 = CategoryFactory(name="Other Cat") # Not for this project
    
    subcat1 = SubCategoryFactory(project=project, category=category1, name="SubCat A")
    subcat2 = SubCategoryFactory(name="Other SubCat")
    
    form = MilestoneForm(project=project)
    
    # Assert old date fields are removed
    assert "project_category_start_date" not in form.fields
    assert "project_category_end_date" not in form.fields
    assert "project_sub_category_start_date" not in form.fields
    assert "project_sub_category_end_date" not in form.fields
    assert "project_group_start_date" not in form.fields
    assert "project_group_end_date" not in form.fields
    assert "project_discipline_start_date" not in form.fields
    assert "project_discipline_end_date" not in form.fields
    
    # Assert classification select fields are present
    assert "project_category" in form.fields
    assert "project_sub_category" in form.fields
    assert "project_group" in form.fields
    assert "area" in form.fields
    assert "project_discipline" in form.fields
    
    # Assert querysets are filtered by project
    assert list(form.fields["project_category"].queryset) == [category1]
    assert list(form.fields["project_sub_category"].queryset) == [subcat1]
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_milestones.py -k test_milestone_form_fields_and_filtering -v`
Expected: FAIL (or ImportErrors / AssertionErrors since `project_sub_category` is not in the form and start/end dates are still there).

**Step 3: Modify MilestoneForm to remove dates and add WBS Level 2**
Modify `app/Project/milestone_schedules/milestone_forms.py` to:
- Include `project_sub_category` in `Meta.fields`.
- Remove all start and end date fields from `Meta.fields`, `widgets`, `labels`, and `help_texts`.
- Add widget and labels for `project_sub_category` and `project_group`.
- Add filtering for `project_sub_category` in `__init__`.

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_milestones.py -k test_milestone_form_fields_and_filtering -v`
Expected: PASS

**Step 5: Commit form changes**
```bash
git add app/Project/milestone_schedules/milestone_forms.py app/Project/tests/test_milestones.py
git commit -m "refactor: remove start/end dates from milestone form and add WBS Level 2"
```

---

### Task 2: Template Refactoring

**Files:**
- Modify: `app/Project/templates/forecasts/milestone_form.html`

**Step 1: Check how the old template behaves**
(No coding step, just verifying form template doesn't render WBS Level 2 and WBS Level 3 yet).

**Step 2: Refactor the template's WBS Classification section**
Modify `app/Project/templates/forecasts/milestone_form.html` in the "WBS Classification" area to remove the old grid layouts for start/end dates and render a clean, balanced grid layout for the five select fields:

```html
                <!-- WBS Classification -->
                <div>
                    <h3 class="text-base font-medium text-gray-900 mb-4">WBS Classification</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>{{ form.project_category|as_crispy_field }}</div>
                        <div>{{ form.project_sub_category|as_crispy_field }}</div>
                        <div>{{ form.project_group|as_crispy_field }}</div>
                        <div>{{ form.area|as_crispy_field }}</div>
                        <div class="md:col-span-2">{{ form.project_discipline|as_crispy_field }}</div>
                    </div>
                </div>
```

**Step 3: Verify the template structure and run pytest on all milestone views**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_milestones.py -v`
Expected: PASS (all milestone view tests should run and succeed, confirming the form submits correctly with the new structure).

**Step 4: Commit template changes**
```bash
git add app/Project/templates/forecasts/milestone_form.html
git commit -m "style: update milestone form template layout with clean select field grid"
```
