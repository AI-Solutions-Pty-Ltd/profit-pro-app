# Walkthrough: Stakeholder Company User & Team Members Form Refactoring

We have successfully redesigned and refactored the stakeholder Company Details update forms (Client, Contractor, and Lead Consultant) to replace the basic checkboxes with an interactive **Company Team Members** table. We also implemented generic user invitation and role allocation controls.

---

## Technical Accomplishments

### 1. View & Form Implementation
* **Form Creation**: Created `CompanyUserInviteForm` in [forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/forms.py) with email, first name, last name, and primary contact fields.
* **Invitation View**: Implemented generic `CompanyInviteUserView` class in [stakeholder_role_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/stakeholder_role_views.py) which:
  - Dynamically sets user types (`Account.Type.CLIENT`, `Account.Type.CONTRACTOR`, or `Account.Type.CONSULTANT`) and Django groups (`consultant` or `contractor`) based on the company type.
  - Automatically checks if a user is already associated with the company to prevent duplicate link errors.
  - Triggers email dispatch or falls back gracefully if emails are disabled.
* **Pre-selection Support**: Overrode `get_initial()` in `ProjectCompanyUserRoleAllocateView` to capture a `?user=<pk>` parameter from the query string and pre-populate the user field.
* **Context Injection**: Overrode `get_context_data` in `ClientUpdateView`, `ContractorUpdateView`, and `LeadConsultantUpdateView` to inject the list of `team_members` with their project-specific roles.

### 2. URL Routes Registration
* **File Modified**: [stakeholder_role_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/urls/stakeholder_role_urls.py)
* **New Route**: Registered `company-invite-user` with path `project/<int:project_pk>/company/<int:company_pk>/invite/`.

### 3. Form Refactoring (Hiding Legacy Listing)
* **Files Modified**: [forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/forms/forms.py) and [company_forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/company/company_forms.py).
* **Logic**: Popped the `users` field from the form fields dictionary during `__init__` if `self.instance.pk` exists. This prevents it from rendering via `{{ form|crispy }}` in edit mode.

### 4. Template Redesign
* **Files Refactored**:
  - [client_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/client/client_form.html)
  - [contractor_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/contractor/contractor_form.html)
  - [lead_consultant_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/lead_consultant/lead_consultant_form.html)
  - [company_invite_user.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/stakeholder_role/company_invite_user.html)
* **Layout**: Added a clean Tailwind-styled HTML table displaying users, primary phone number contacts, allocated roles, and actions (Edit Role, Remove Role, and Assign Role). Add buttons next to/above the table to **Create User** and **Assign Role**.

---

## Verification Results

### 1. View Integration and CRUD Tests
All 13 integration test cases in the test suite pass with green checks:
```bash
.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_stakeholder_role_views.py -v
```
**Results**:
```
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_allocate_user_role_view_get PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_allocate_user_role_view_post_success PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_allocate_user_role_view_post_duplicate_error PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_update_user_role_view_get PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_update_user_role_view_post PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_remove_user_role_view PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_view_permission_denied_for_non_admin PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_company_invite_user_view_get PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_company_invite_user_view_post_new_user_success PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_company_invite_user_view_post_existing_user_success PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_company_invite_user_view_post_duplicate_error PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_preselect_user_allocate_view_get PASSED
app/Consultant/tests/test_stakeholder_role_views.py::TestStakeholderRoleViews::test_company_update_view_team_members_context PASSED

====================== 13 passed, 40 warnings in 52.85s =======================
```

### 2. Ruff Linter & Formatter Validation
Running ruff code quality checks on the modified files returns clean:
```bash
.venv\Scripts\python.exe -m ruff check ...
```
**Results**:
```
All checks passed!
```
