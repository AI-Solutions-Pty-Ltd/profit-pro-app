# Goal
Refactor the stakeholder Company Details edit/update forms (Client, Contractor, and Lead Consultant) to replace the simple `Company Users` multi-select checkbox list with an interactive **Company Team Members** table. The table should display associated users, their contacts, and their project-specific roles (e.g., Admin/Supervisor/Capturer). Additionally, add user invitation and role allocation controls.

# Constraints
1. **Scoping**: The team members table and role actions are only applicable to existing company records (when editing/updating). When creating a new company, the team members section must be hidden/omitted.
2. **Context**: Company users can be invited and assigned roles specifically in the context of the active project (`project` object from the URL context).
3. **Security**: Only Project Administrators (authorized via `UserHasProjectRoleGenericMixin`) can access user invites, role allocations, updates, and removals.
4. **Code Quality**: Follow established patterns: inherit models from `BaseModel`, write Google-style docstrings, write comprehensive pytest test cases, and use model factories.

# Known context
1. **Existing Forms & Templates**:
   - Client form: [client_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/client/client_form.html) (rendered by `ClientUpdateView` using `ClientForm`).
   - Contractor form: [contractor_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/contractor/contractor_form.html) (rendered by `ContractorUpdateView` using `CompanyForm`).
   - Lead Consultant form: [lead_consultant_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/lead_consultant/lead_consultant_form.html) (rendered by `LeadConsultantUpdateView` using `ConsultantCompanyForm`).
2. **Existing Models & Views**:
   - `ProjectCompanyUserRole` represents stakeholder roles.
   - Views for CRUD operations on stakeholder roles are in [stakeholder_role_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/stakeholder_role_views.py) and mapped in [stakeholder_role_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/urls/stakeholder_role_urls.py).
3. **Email Settings**:
   - Settings in `django.conf.settings` dictate whether emails are sent (`USE_EMAIL` is True/False).

# Risks
1. **Redirection Loop / Target Mismatch**: Since three different detail pages (Client, Contractor, Lead Consultant) will link to the user invitation form, the post-invite redirect must dynamically point back to the correct detail page based on the company's type.
   * *Mitigation*: Dynamically inspect `company.type` in `CompanyInviteUserView`'s success path and redirect accordingly.
2. **Duplicate Invitations**: Inviting a user who is already associated with the company could cause validation errors or redundant records.
   * *Mitigation*: Perform an explicit `.exists()` check in `form_valid()` and add an appropriate form field validation error.
3. **Transaction Rollbacks**: Database-level unique constraint violations can abort the database connection transaction.
   * *Mitigation*: Ensure user and role allocations check existence before saving to prevent raw `IntegrityError` from bubbling up.

# Options (2?4)

### Option 1: Dedicated Generic Invitation View + Template Table (Recommended)
Introduce a generic `CompanyInviteUserView` class in the `stakeholder_role` namespace to handle inviting users for Clients, Contractors, and Consultants.
- When rendering update views, hide the legacy many-to-many checkboxes `form.users` if `object` is present.
- Render a Tailwind-styled HTML table for team members, with buttons linking to the new invite view and the existing allocation views.
* **Pros**:
  - Extremely clean segregation of concerns.
  - Fits perfectly into the existing routing structure without polluting individual stakeholder management modules.
  - High reusability of views and forms.
* **Cons**:
  - Requires writing a new generic view and template.

### Option 2: Inline AJAX/Modal Sub-Form
Embed the user invitation and role allocation forms directly on the Company edit page using HTML dialogs (Modals) and JavaScript (AJAX) endpoints.
* **Pros**:
  - Smoother user experience by avoiding full-page transitions.
* **Cons**:
  - Substantially higher frontend complexity.
  - Diverges from the existing, standard multi-page FormView architecture used in the codebase.

# Recommendation
We recommend **Option 1**. It is standard, secure, fits the existing codebase flow perfectly, and is less error-prone than managing inline AJAX states.

# Acceptance criteria
1. **Form**: Create `CompanyUserInviteForm` in `app/Consultant/forms.py` with email, first name, last name, and primary contact fields.
2. **View**: Implement `CompanyInviteUserView` under `app/Consultant/views/stakeholder_role_views.py`. It must:
   - Restrict access to Project Admins using `UserHasProjectRoleGenericMixin`.
   - Dynamically set the new user's `Account.type` (Client/Contractor/Consultant) and group (consultant/contractor) depending on the target company type.
   - Send invitation/notification email if enabled.
3. **URLs**: Register `company-invite-user` in `app/Consultant/urls/stakeholder_role_urls.py`.
4. **UI Refactoring**:
   - In `client_form.html`, `contractor_form.html`, and `lead_consultant_form.html`, hide the `users` field when `object` is present.
   - Render the **Company Team Members** table with columns: `User` (Name & Email), `Contact` (Phone), `Role`, and `Action` (links for Edit/Remove Role, or Assign Role if no role exists yet).
   - Add **Invite User** and **Assign Role** buttons.
5. **Testing**: Add test cases in `app/Consultant/tests/` to verify company user invitations and correct rendering of the team members table.
