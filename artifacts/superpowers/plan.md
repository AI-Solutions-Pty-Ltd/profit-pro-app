# Implementation Plan - Add Bi-Weekly Safety and NCR Cards to Company Management

## Goal
Add "Bi-Weekly Safety" and "NCR Register" cards to the "Site Management" grid in the Business Management Center dashboard (`company_management.html`), specifically appending them at the end of the site cards list (Option 1).

## Assumptions
- The template context represents the active project under the variable name `company`.
- The Django URL namespaces are:
  - Bi-Weekly Safety: `site_management:biweekly-safety-list`
  - NCR Register: `site_management:ncr-list`
- The project has `.venv` correctly configured, and pytest tests can run.

## Plan

### Step 1: Update Company Management Template
- **Files**: `app/Project/templates/company/company_management.html`
- **Change**: Append "Bi-Weekly Safety" and "NCR Register" cards to the end of the `<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">` in the Site Management section (around lines 440-445).
- **Verify**: Read the modified template file to check for correct URL resolution tags and class styling.

### Step 2: Add View Unit Test
- **Files**: `app/Project/tests/test_views.py`
- **Change**: Add a new test case `TestCompanyManagementSiteCards` that verifies rendering of `company_management.html` and checks that the HTML response content includes:
  - The URL targeting `site_management:biweekly-safety-list` with `company.pk`
  - The URL targeting `site_management:ncr-list` with `company.pk`
- **Verify**: Run the new test case with pytest:
  `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -k TestCompanyManagementSiteCards`

### Step 3: Run Full View Tests & Linting
- **Files**: None
- **Change**: None
- **Verify**: Run the full suite of Project views tests and ruff lint check:
  `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py`

## Risks & mitigations
- **Risk**: Missing `project` or `company` subscription permissions during testing.
- **Mitigation**: Use `AccountFactory` which defaults to `FULL_ACCESS` subscription, or set `subscription = Subscription.FULL_ACCESS` explicitly on the user during tests.

## Rollback plan
- Revert changes to `app/Project/templates/company/company_management.html` and `app/Project/tests/test_views.py` using `git checkout`.
