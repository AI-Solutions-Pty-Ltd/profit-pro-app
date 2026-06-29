# Project Management Page Reports Integration Design

This document details the design for adding select project functionality and viewing coverpage/valuation summary reports directly from the Project Management page.

## Requirements & Scope

1. **Project Selector**: A dropdown selector at the top of the project list allowing users to select any project they have access to and navigate to its Cover Page or Valuation Summary.
2. **Table Row Actions**: Quick links in each row of the projects table to view the Cover Page and Valuation Summary.
3. **Redirect Flow**:
   - Resolve the latest APPROVED payment certificate for the chosen project.
   - If no APPROVED certificate exists, fall back to the latest certificate of *any* status.
   - If no certificates exist at all, show a toast error message and redirect back to the Project Management page.

## Proposed Changes

### Views & Controllers
- Update `ProjectListView` in [project_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/project_views.py) to pass `all_projects` to the template context.
- Implement `ProjectCoverPageRedirectView` and `ProjectValuationSummaryRedirectView` in [project_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/project_views.py).

### Routing
- Register redirection routes in [project_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/project_urls.py).

### Templates
- Add dropdown selector and row action links in [project_list.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/project_list.html) along with supporting JS logic.
