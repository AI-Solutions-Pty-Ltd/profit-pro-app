## Goal
Refactor the report configuration UI card inputs and add a preview button that opens a print dialog showing the structure of the report.

## Assumptions
- The refactoring mainly involves organizing the HTML of the Layout Visual Previews in project_setup.html into cleaner, maintainable components.
- The preview print dialog should be a new view that generates a dummy certificate/report matching the selected layout and triggers window.print() on load.

## Plan
1. **Create Preview View**:
   - Files: pp/Project/projects/project_views.py, pp/Project/urls.py
   - Change: Add ProjectReportLayoutPreviewView that takes the project PK and optionally a layout_style query parameter. It renders a dummy layout template. Update urls.py to route to this view.
   - Verify: Run .venv\Scripts\python.exe manage.py check to ensure URLs are valid.
2. **Create Preview Templates**:
   - Files: pp/Project/templates/project/project_layout_preview.html
   - Change: Create the template that includes Tailwind CSS and a script to call window.print(). Render a structural representation of the report based on the layout_style.
   - Verify: Check that the template is loadable.
3. **Refactor Card Inputs in project_setup.html**:
   - Files: pp/Project/templates/project/project_setup.html
   - Change: Refactor the layout visual preview cards (Standard, Valterra, Lephadimisha) into a more modular structure, potentially extracting them into included partials if they are too long.
   - Verify: Ensure the configuration page still loads correctly without errors.
4. **Add Preview Button**:
   - Files: pp/Project/templates/project/project_setup.html
   - Change: Add a "Preview" button in the Layout Visual Preview area. Use Javascript to read the currently selected certificate_layout_select value and open the preview URL in a new tab with that layout.
   - Verify: Test clicking the button to ensure it navigates to the correct preview URL.

## Risks & mitigations
- **Risk:** The dummy layout might not accurately represent the real layout. **Mitigation:** Base the dummy layout on existing certificate PDF templates using Tailwind for print styling.
- **Risk:** The "Preview" button might not capture the unsaved layout choice. **Mitigation:** Use client-side JavaScript on the button to dynamically construct the URL using the currently selected <select> value.

## Rollback plan
- Remove the new URL, view, and template. Revert project_setup.html to its previous git state.
