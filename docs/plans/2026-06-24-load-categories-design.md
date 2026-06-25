# Design Doc: Load WBS Categories into Scope Planning

## Goal
To allow users to clone/populate WBS categories (levels 1, 2, and 3) from another project into the current project's scope planning screen.

## Proposed Changes
We will implement Approach 1:
1. **Scope Planning UI (`scope_planning.html`)**:
   - Add a "Load Categories" button next to "Add WBS Level 1".
   - This button opens a modal showing a select dropdown of other projects that have active (non-deleted) categories.
   - Submitting the modal sends a POST request with the source project's ID to a new endpoint.
2. **Backend View (`LoadWBSCategoriesView` in `app/Planning/views.py`)**:
   - Accepts the source project ID via POST.
   - Deletes any existing Category, SubCategory, and Group records for the target project.
   - Copies all active Categories, SubCategories, and Groups from the source project to the target project, preserving their hierarchy and ordering.
   - Redirects the user back to the scope planning page with a success message.
3. **URL Routing (`app/Planning/urls.py`)**:
   - Register the new POST endpoint at `<int:project_pk>/scope-planning/load-categories/`.

## Verification Plan
- Create test cases to verify cloning WBS categories across projects.
- Verify that subcategories and groups are copied and correctly nested.
- Run `pytest` to ensure all tests pass.
- Run `ruff` to ensure styling and formatting compliance.
