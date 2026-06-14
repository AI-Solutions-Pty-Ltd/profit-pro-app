# Superpowers Brainstorm

## Goal
The goal is to create a dedicated Column Heading Customization & Reordering page for a project, replace the table/form under "Report Selection & Configuration" in the project setup page with a "Report Template Setup" card, and add a link/button on that card to access the new dedicated page.

## Constraints
- **Virtual Environment**: All execution and commands must use the project's virtual environment `.venv\Scripts\python.exe`.
- **Styling**: Must match the premium Tailwind CSS look and feel of the existing project setup page (responsive layout, hover transitions, icons, and consistent cards).
- **Functionality**: Must not break the existing saving logic or column configuration persistence on the `Project` model.

## Known context
- **Setup Page**: Located at `app/Project/templates/project/project_setup.html` and rendered via `ProjectSetupView` in `app/Project/projects/project_views.py`.
- **Existing Customization Component**: The column customization table, live preview, save form, and its script block reside within `project_setup.html` (lines 471-544, lines 1026-1192).
- **Data Model**: The resolved configuration is returned by `project.get_column_config()` and saved back to `project.column_config` via the POST view parameter `action="save_report_config"`.
- **Permissions**: Views should enforce `SubscriptionRequiredMixin` and `UserHasProjectRoleGenericMixin` with `Role.USER` level.

## Risks
- **JavaScript Breakage**: The drag/reorder and live preview logic expects specific elements like `columns-config-list` and `live-header-preview`. Extracting it must ensure all DOM elements are present in the new page's template.
- **Redirection / UX Flow**: Moving this form to a separate page requires clear breadcrumb navigation and a seamless save-and-redirect/success message flow.
- **Permission Bypass**: A user must not be able to customize columns for a project they do not belong to.

## Options (2?4)
- **Option 1**: Implement `ProjectReportConfigView` mapping to `<int:pk>/report-config/` using template `project/report_config.html`. On the setup page, under the "Report Selection & Configuration" section, render a grid layout containing the "Report Template Setup" card, which links to the new page. The new view handles the POST action `save_report_config` and redirects back to itself with a success message.
- **Option 2**: Create a reusable Django form for the report config and render it within a modal on the setup page rather than creating a dedicated page. (Not recommended because the user explicitly asked for a dedicated page).
- **Option 3**: Move the table to a new page, but keep the POST endpoint pointing to the old `ProjectSetupView`. (Not recommended, as it makes view handling less clean and splits the configuration logic).

## Recommendation
- **Option 1** is recommended. It cleanly separates the complex column reordering/customization page (which includes a large JavaScript block and table preview) from the general project setup overview, while keeping view and save operations nicely encapsulated in `ProjectReportConfigView`.

## Acceptance criteria
- A new route `<int:pk>/report-config/` mapped to `ProjectReportConfigView` in `project_urls.py`.
- `ProjectReportConfigView` requires `Role.USER` and project membership.
- A new template `app/Project/templates/project/report_config.html` containing the customize form, live preview, and reorder Javascript.
- The "Report Selection & Configuration" section in `project_setup.html` is updated to show a "Report Template Setup" card matching the other setup cards.
- The card contains a link/button leading to the new configuration page.
- Saving/resetting column configs on the new page works correctly and displays a success alert.
- Pytest tests are updated or added, and all tests pass.
