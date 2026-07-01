# Design Document — Custom Project Groups and Regional Reports

This document outlines the design for allowing users to group multiple selected projects (like "favorites" or custom names) and generate Cover Page and Valuation Summary reports structured by province.

## 1. Database Model
- Introduce a new model `ProjectGroup` in `projects_models.py` inheriting from `BaseModel`.
- Model has fields:
  - `user`: ForeignKey to custom User model `Account`
  - `name`: CharField representing the group's name
  - `projects`: ManyToManyField to `Project`
- Handle duplicate name validation at the API view layer (checking only active groups where `deleted=False`).

## 2. User Interface Changes
- **Project Groups Navigation:** Display a dropdown next to the back navigation button in `project_list.html` listing saved groups and their action links.
- **Batch Actions:** Add a "Create Group" button in the batch actions bar.
- **Modal Dialog:** Implement a clean modal dialog to prompt for the group's name when creating.
- **AJAX Communication:** Submit creations to the API. If a validation error occurs, show it inside the modal without refreshing.

## 3. Grouped Reports
- **Cover Page:** Aggregate progressive and contract metrics across the group's projects.
- **Valuation Summary (Grouped):** Group projects by `province`. Render province headers, list matching projects, display province-level sub-totals, and calculate grand totals.

## 4. URL Routes
- `reports/group/create/` -> `ProjectGroupCreateView`
- `reports/group/<int:group_pk>/delete/` -> `ProjectGroupDeleteView`
- `reports/group/<int:group_pk>/cover-page/` -> `GroupCoverPageView`
- `reports/group/<int:group_pk>/cover-page/xlsx/` -> `GroupCoverPageDownloadXLSXView`
- `reports/group/<int:group_pk>/valuation-summary/` -> `GroupValuationSummaryView`
- `reports/group/<int:group_pk>/valuation-summary/xlsx/` -> `GroupValuationSummaryDownloadXLSXView`
