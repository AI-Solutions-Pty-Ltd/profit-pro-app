### Goal
Refactor and improve user management inside the stakeholder submodules (Client Management, Contractor Management, and Consultant Management). The feature introduces a new database model `ProjectCompanyUserRole` to map a user, a project, a stakeholder company, and a specific stakeholder role (Admin, Supervisor, or Capturer). This allows assigning users and managing their roles contextual to the project/company stakeholder scope, displaying them clearly on the Project Setup dashboard, and laying the groundwork for modular permission checks.

### Assumptions
- Python 3.13+ virtual environment is active.
- Existing companies (Clients, Contractors, Consultants) are already linked to projects via `project.client`, `project.contractor`, and `project.consultants`.
- Stakeholder roles are restricted to `Admin`, `Supervisor`, and `Capturer`.
- Standard Django migrations and pytest suite are functioning.

### Plan

1. Define the `ProjectCompanyUserRole` Model
   - Files:
     - [NEW] [project_company_user_role_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/models/project_company_user_role_models.py)
     - [MODIFY] [__init__.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/models/__init__.py)
     - [MODIFY] [admin.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/admin.py)
   - Change:
     - Create [project_company_user_role_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/models/project_company_user_role_models.py) defining `ProjectCompanyUserRole` model inheriting from `BaseModel`, with foreign keys to `Project`, `Company`, `Account` and a `role` choices field.
     - Add `UniqueConstraint` on `(project, company, user)` to enforce database uniqueness.
     - Register `ProjectCompanyUserRole` in [__init__.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/models/__init__.py) (`__all__` list and package imports).
     - Register `ProjectCompanyUserRole` in [admin.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/admin.py) for Django administration support.
   - Verify:
     - Check code for syntax errors.

2. Generate and Apply Database Migrations
   - Files:
     - `app/Project/migrations/*` (auto-generated migration file)
   - Change:
     - Run `makemigrations` and `migrate` commands to apply schema updates.
   - Verify:
     - `.venv\Scripts\python.exe manage.py makemigrations`
     - `.venv\Scripts\python.exe manage.py migrate`

3. Create Factory and Unit Tests for the Model
   - Files:
     - [MODIFY] [factories.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/factories.py)
     - [NEW] [test_project_company_user_role.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_project_company_user_role.py)
   - Change:
     - Add `ProjectCompanyUserRoleFactory` to [factories.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/factories.py).
     - Write model tests verifying database creation, constraints validation, unique constraint enforcement, and `__str__` method.
   - Verify:
     - Run new tests: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_project_company_user_role.py`

4. Define Allocation Forms and Views
   - Files:
     - [MODIFY] [forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/forms.py)
     - [NEW] [stakeholder_role_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/stakeholder_role_views.py)
   - Change:
     - Define `ProjectCompanyUserRoleForm` to select a user (optionally filtered by company membership) and choose a role (Admin, Supervisor, Capturer).
     - Create Views: `ProjectCompanyUserRoleAllocateView`, `ProjectCompanyUserRoleUpdateView`, and `ProjectCompanyUserRoleRemoveView` inside `app/Consultant/views/stakeholder_role_views.py` to handle CRUD operations for stakeholder roles.
   - Verify:
     - Run simple python import validation on views.

5. Map Stakeholder Role URL Routes
   - Files:
     - [MODIFY] [__init__.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/urls/__init__.py)
   - Change:
     - Add URL patterns for allocating, editing, and removing stakeholder company user roles.
   - Verify:
     - Verify Django URL resolver maps patterns correctly.

6. Update UI Templates on Project Setup
   - Files:
     - [MODIFY] [project_setup.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/project_setup.html)
   - Change:
     - In each card (Client Management, Contractor Management, Consultant Management), check if a company is assigned.
     - If assigned, list all assigned users, their emails, and their stakeholder roles (using pills/badges).
     - Provide links to assign users, edit roles, or remove user assignments from the project company context.
   - Verify:
     - Render project setup page and verify page loads cleanly without template errors.

7. Implement Permission Check Mixin and Guard Views
   - Files:
     - [MODIFY] [mixins.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/mixins.py)
   - Change:
     - Add `UserHasStakeholderRoleGenericMixin` checking if the request user is associated with a specific role (e.g., Admin/Supervisor) for the given project and company before proceeding with actions.
   - Verify:
     - Write and run unit tests for views guarded by the mixin.

8. Add Integration and View Tests
   - Files:
     - [NEW] [test_stakeholder_role_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/tests/test_stakeholder_role_views.py)
   - Change:
     - Write integration test cases simulating role allocation, updating, removal, and permission validation.
   - Verify:
     - Run all Consultant tests: `.venv\Scripts\python.exe -m pytest app/Consultant/tests/`

### Risks & mitigations
- **Risk**: A user gets assigned multiple conflicting stakeholder roles under the same project and company.
  - *Mitigation*: Enforce a strict unique constraint on `(project, company, user)` in the database schema.
- **Risk**: Deleting a project, company, or user leaves orphaned role assignments.
  - *Mitigation*: Set `on_delete=models.CASCADE` on all ForeignKey fields to cleanly cascade deletions.

### Rollback plan
- Delete the created database migration file and revert the schema using:
  `.venv\Scripts\python.exe manage.py migrate Project <previous_migration_name>`
- Discard changes using git:
  `git checkout -- app/`
- Delete untracked files:
  `git clean -fd`

