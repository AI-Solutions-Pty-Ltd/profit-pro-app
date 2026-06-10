# Superpowers Finish Summary - Add Bi-Weekly Safety and NCR Cards to Company Management

## Verification commands run + results
- Pytest unit tests:
  - Command: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -k TestCompanyManagementSiteCards`
    Result: **1 passed**
  - Command: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py`
    Result: **2 passed**
- Ruff Python styling linter check:
  - Command: `.venv\Scripts\python.exe -m ruff check app/Project/tests/test_views.py`
    Result: **All checks passed!**

## Summary of changes
1. **app/Project/templates/company/company_management.html**:
   - Added the "Bi-Weekly Safety" card at the end of the site cards list under the Site Management section, using `indigo` border, standard transitions, and the `shield-exclamation` Heroicon.
   - Added the "NCR Register" card at the end of the site cards list under the Site Management section, using `amber` border, standard transitions, and the `document-check` Heroicon.
2. **app/Project/tests/test_views.py**:
   - Created the test class `TestCompanyManagementSiteCards` to verify `CompanyManagementView` correctly renders the "Bi-Weekly Safety" and "NCR Register" cards with parameters `company.pk`.

## Follow-ups
- None.

## Manual validation steps (if applicable)
- Log in to the application and navigate to the Business Management Center for a company (`/project/company/<id>/management/`).
- Verify that "Bi-Weekly Safety" and "NCR Register" cards are present at the end of the "Site Management" grid.
- Click each card to verify they redirect to the respective list pages:
  - `/site-management/<id>/biweekly-safety/`
  - `/site-management/<id>/ncr/`
