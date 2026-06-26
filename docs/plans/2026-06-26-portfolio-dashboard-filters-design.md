# Design: Portfolio Dashboard Filters Refactoring

Date: 2026-06-26

## Goal
Add filter by Province, Municipality, and Search by Name to the Portfolio Dashboard. Refactor the filters layout to be modern, user-friendly, and consistent with the Project List page filters.

## Proposed Design
1. **Name Search**: Add a prominent search input on the top row of the filter form.
2. **Advanced Filters Toggle**: Add an "Advanced Filters" button with a chevron to toggle a collapsible filter drawer.
3. **Advanced Filters Drawer**: Place Sector, Province, Municipality, Discipline, Stage, Client, Contractor, and Consultant dropdowns in a collapsible container.
4. **Idempotence / User Friendly Submission**: Remove all `onchange="this.form.submit()"` reloads. Add a dedicated "Apply" button to submit the form and a "Clear" button to reset the filters.
5. **Dynamic Municipality Filtering**: Add client-side Javascript to dynamically update the Municipality options based on the selected Province.
6. **Active Filter Badges**: Render active filter chips below the search bar.

## Target Templates to Modify
- `app/Project/templates/portfolio/portfolio_dashboard.html`

## Verification Plan
1. Render the page and verify that all filters and the search input show up.
2. Verify that selecting a Province dynamically filters the Municipality dropdown options.
3. Verify that applying filters correctly updates the projects list on the dashboard.
4. Verify that clearing filters resets the form.
