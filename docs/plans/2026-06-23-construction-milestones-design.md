# Design Document: Construction Milestones Feature

This document outlines the design for the Construction Milestones feature in the Profit Pro application. The goal is to allow project administrators to capture, sequence, and manage milestones for projects, including a one-click button to load a standard list of 20 construction milestones.

## User Review Required

> [!IMPORTANT]
> The new views and urls will be restricted to users with `Role.ADMIN` roles within the project context, consistent with other setup features like WBS Categories, Disciplines, and Drawing Types.

## Proposed Design & Architecture

We will implement a setup card under the **Project Work Breakdown Structures** section in the project setup page, which will lead to a dedicated setup page for managing the project's milestones.

We will reuse the existing `Milestone` model (from `app/Project/milestone_schedules/milestone_models.py`) to store these construction milestones, avoiding schema duplication.

### 1. Model & Data Layer
No changes to the existing `Milestone` database model are required.
We will pre-define a list of 20 standard construction milestones:
1. Earthworks
2. Foundations
3. Surface Beds
4. External Envelope
5. Internal divisions
6. Doors and Windows
7. Roof Construction
8. Ceilings
9. Floor Finishes
10. Wall Finishes
11. Ceiling Finishes
12. Plastering
13. Plumbing 1st Fix
14. Plumbing 2nd Fix
15. Electrical - 1st Fix
16. Electrical - 2nd Fix
17. Electrical - 3rd Fix
18. Painting - Under Coat
19. Painting - 1st Coat
20. Painting - 2st Coat

### 2. View Layer
We will add two new views in `app/Project/milestone_schedules/milestone_views.py`:
- `MilestoneSetupView`: Lists all milestones configured for the project, showing details (sequence, name, dates, status) in a table. It will render `project/milestones/milestone_manage.html`.
- `MilestoneLoadDefaultsView`: A POST action that bulk-inserts the 20 default milestones.
  - Initial `planned_date` will be set to the project's start date (falling back to the current date if not configured).
  - Sequence will be automatically populated from 0 to 19 (or continuing from the highest sequence if some milestones already exist).
  - Skips duplicates if milestones with the same name already exist for the project.

We will also update `MilestoneCreateView`, `MilestoneUpdateView`, and `MilestoneDeleteView` to respect a `next` redirect query parameter so they can be seamlessly used from the setup flow and redirect back to the setup list instead of the default Forecasts Hub tab.

### 3. URL Routing
We will add the following routes to `app/Project/milestone_schedules/milestone_urls.py`:
- `<int:project_pk>/setup/` -> `project-milestone-setup` (mapped to `MilestoneSetupView`)
- `<int:project_pk>/setup/load-defaults/` -> `project-milestone-load-defaults` (mapped to `MilestoneLoadDefaultsView`)

### 4. Template & UI Layer
- **`app/Project/templates/project/project_setup.html`**: Add a card for "Setup Construction Milestones" in the WBS grid.
- **`app/Project/templates/project/milestones/milestone_manage.html`**: A new setup list page showing current milestones, edit/delete actions, and a button to bulk-load defaults if they haven't been loaded yet.
- **`app/Project/templates/forecasts/milestone_form.html`**: Update cancel/back buttons to respect the dynamic `back_url` from view context.
- **`app/Project/templates/forecasts/milestone_confirm_delete.html`**: Update cancel/back buttons to respect the dynamic `back_url`.

## Verification & Testing Plan

### Automated Tests
- Create unit tests in `app/Project/tests/test_milestones.py` covering:
  - `MilestoneSetupView` resolves and loads the current milestones list.
  - `MilestoneLoadDefaultsView` creates the 20 standard milestones with correct sequences and start dates.
  - `MilestoneCreateView`, `MilestoneUpdateView`, and `MilestoneDeleteView` correctly respect the `next` redirect parameter.

### Manual Verification
- Access the project setup page, verify the new setup milestones card is visible.
- Click the card and verify the milestone list is empty (for a fresh project).
- Click "Load Default Milestones" and verify that all 20 milestones are populated correctly with sequences 1-20 and the project's start date.
- Try editing a milestone from the setup flow and verify saving redirects back to the setup flow.
- Try deleting a milestone and verify it redirect back.
