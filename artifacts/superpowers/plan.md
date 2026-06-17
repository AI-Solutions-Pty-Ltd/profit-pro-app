# Goal
Refactor the stakeholder Company Details update forms (Client, Contractor, and Lead Consultant) to replace the simple `Company Users` multi-select checkbox list with an interactive **Company Team Members** table displaying users, contacts, project-specific roles, and actions. Add user invitation and role allocation controls.

# Assumptions
- Django virtual environment is active.
- `ProjectCompanyUserRole` model and migration `0096` are already set up and functioning.
- The templates are styled using TailwindCSS.

# Plan

### 1. Step 1: Create `CompanyUserInviteForm`
- **Files**: `app/Consultant/forms.py`
- **Change**: Define `CompanyUserInviteForm` containing `email`, `first_name`, `last_name`, and `primary_contact` fields (similar to `ClientUserInviteForm`).
- **Verify**: Run `ruff check app/Consultant/forms.py` to ensure it passes linting.

### 2. Step 2: Implement generic `CompanyInviteUserView`
- **Files**: `app/Consultant/views/stakeholder_role_views.py`
- **Change**: Implement `CompanyInviteUserView` class. Include permissions check, validation check for existing users, dynamic mapping of Account type/group, email invitation sending logic, and redirection routes.
- **Verify**: Run `ruff check app/Consultant/views/stakeholder_role_views.py`.

### 3. Step 3: Create template `company_invite_user.html`
- **Files**: [NEW] `app/Consultant/templates/stakeholder_role/company_invite_user.html`
- **Change**: Create a Tailwind-styled invitation form matching standard visual design.
- **Verify**: Inspect HTML layout code or check file existence.

### 4. Step 4: Register the invitation URL
- **Files**: `app/Consultant/urls/stakeholder_role_urls.py`
- **Change**: Add route for `company-invite-user`.
- **Verify**: Check file content/routes.

### 5. Step 5: Redesign and refactor forms and views context
- **Files**:
  - `app/Consultant/views/client_management_views.py`
  - `app/Consultant/views/contractor_management_views.py`
  - `app/Consultant/views/lead_consultant_management_views.py`
  - `app/Consultant/views/stakeholder_role_views.py`
- **Change**: In `ClientUpdateView`, `ContractorUpdateView`, and `LeadConsultantUpdateView`, override `get_context_data` to fetch associated users and their roles on the current project. Build a list of members. Also, in `ProjectCompanyUserRoleAllocateView`, support pre-selecting the `user` field from `request.GET.get('user')`.
- **Verify**: Run `ruff check` on the views.

### 6. Step 6: Hide `users` field from forms on edit
- **Files**:
  - `app/Project/forms/forms.py`
  - `app/Project/company/company_forms.py`
- **Change**: In `ClientForm` and `CompanyForm` `__init__` methods, pop the `users` field if `self.instance.pk` is present, to prevent it from rendering in `form|crispy`.
- **Verify**: Run `ruff check` on the forms.

### 7. Step 7: Refactor the templates to display the Team Members table
- **Files**:
  - `app/Consultant/templates/client/client_form.html`
  - `app/Consultant/templates/contractor/contractor_form.html`
  - `app/Consultant/templates/lead_consultant/lead_consultant_form.html`
- **Change**:
  - Render the **Company Team Members** table under the banking details section.
  - Add columns: `User`, `Contact`, `Role`, and `Action`.
  - Add buttons for **Invite User** and **Assign Role**.
- **Verify**: Check rendering of the page or run tests.

### 8. Step 8: Write unit and integration tests
- **Files**:
  - `app/Consultant/tests/test_stakeholder_role_views.py`
- **Change**: Add test cases for the invitation view, pre-selecting user initial data in allocation view, and verifying the template rendering includes the team members table.
- **Verify**: Run `.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_stakeholder_role_views.py -v`.

# Risks & mitigations
- **Duplicate relation database errors**: Mitigation: Check if the user is already associated with the company in `CompanyInviteUserView.form_valid`.
- **Pre-selecting user fails**: Mitigation: Override `get_initial` in `ProjectCompanyUserRoleAllocateView` to fetch and set `initial['user']` from query parameters.

# Rollback plan
- Use git stash or git restore on modified files to revert to the initial state.
