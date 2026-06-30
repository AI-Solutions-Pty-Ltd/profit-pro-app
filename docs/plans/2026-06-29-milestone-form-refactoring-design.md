# Milestone Form Refactoring Design

This document outlines the design for refactoring the project milestone creation and update form. The goal is to remove all start and end date fields associated with WBS levels, area, and discipline, and expose a clean set of select classification fields.

## Goals

1. Remove the start date and end date fields for WBS Level 1, Area (Level 2), and Discipline (Level 3) from the milestone form.
2. Expose all five classification select fields on the milestone form:
   - WBS Level 1 (Category - `project_category`)
   - WBS Level 2 (SubCategory - `project_sub_category`)
   - WBS Level 3 (Group - `project_group`)
   - Area (Municipality - `area`)
   - Discipline (Discipline - `project_discipline`)
3. Ensure all select querysets are filtered to only show items belonging to the active project.
4. Clean up the form layout in the template to display the select fields in a neat grid.

## Proposed Changes

### Forms

#### [MODIFY] [milestone_forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/milestone_schedules/milestone_forms.py)

- Remove start/end date fields from `Meta.fields`.
- Add `project_sub_category` to `Meta.fields`.
- In `__init__`, filter `project_sub_category` by the active project and set `.required = False`.
- Remove widgets, labels, and help texts for the removed start/end date fields.
- Add label/help text for `project_sub_category`.

### Templates

#### [MODIFY] [milestone_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/forecasts/milestone_form.html)

- Remove the start/end date fields from the HTML.
- Render all five select fields in a clean responsive grid.

## Verification Plan

### Automated Tests
- Run `.venv\Scripts\python.exe -m pytest app/Project/tests/test_milestones.py -v` to ensure milestone creation, update, and delete actions continue to pass.
