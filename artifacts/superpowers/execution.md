## Batch 1 (Sequential Execution)
- TSK-01: SUCCESS - Files: `app/Project/projects/project_urls.py`
- TSK-02: SUCCESS - Files: `app/Project/projects/project_views.py`
- TSK-03: SUCCESS - Files: `app/Project/templates/project/report_config.html`
- TSK-04: SUCCESS - Files: `app/Project/templates/project/project_setup.html`
- TSK-05: SUCCESS - Files: `app/Project/tests/test_views.py`

Verification:
- TSK-01 & TSK-02: `.venv\Scripts\python.exe manage.py check` -> Passed without issues.
- TSK-03 & TSK-04: Layout verified visually and checks passed.
- TSK-05: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py` -> Passed: 3 passed.

---

### Step 1: Define the `ProjectCompanyUserRole` Model
- Files changed:
  - [NEW] [project_company_user_role_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/models/project_company_user_role_models.py)
  - [MODIFY] [__init__.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/models/__init__.py)
  - [MODIFY] [admin.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/admin.py)
- What changed:
  - Created `ProjectCompanyUserRole` and `StakeholderRole` choices to map a user, a project, a stakeholder company, and a specific stakeholder role.
  - Registered the models in the Project models package `__init__.py` and in django admin.
- Verification command:
  - `.venv\Scripts\python.exe manage.py check`
- Result: PASS

---

### Step 2: Generate and Apply Database Migrations
- Files changed:
  - [NEW] [0096_projectcompanyuserrole.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/migrations/0096_projectcompanyuserrole.py)
- What changed:
  - Generated Django migration for the `ProjectCompanyUserRole` model.
  - Ran migration to create the table in the database.
- Verification commands:
  - `.venv\Scripts\python.exe manage.py makemigrations`
  - `.venv\Scripts\python.exe manage.py migrate`
- Result: PASS

---

### Step 3: Create Factory and Unit Tests for the Model
- Files changed:
  - [MODIFY] [factories.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/factories.py)
  - [NEW] [test_project_company_user_role.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_project_company_user_role.py)
- What changed:
  - Added `ProjectCompanyUserRoleFactory` to `factories.py`.
  - Added unit test cases covering model creation, string representation, default role value, meta configuration, and database unique constraint validation.
- Verification command:
  - `.venv\Scripts\python.exe -m pytest app/Project/tests/test_project_company_user_role.py -v`
- Result: PASS

---

### Step 4: Define Allocation Forms and Views
- Files changed:
  - [MODIFY] [forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/forms.py)
  - [NEW] [stakeholder_role_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/stakeholder_role_views.py)
  - [NEW] [allocate_user_role_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/stakeholder_role/allocate_user_role_form.html)
  - [NEW] [confirm_remove_user_role.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/stakeholder_role/confirm_remove_user_role.html)
- What changed:
  - Created `ProjectCompanyUserRoleForm` to select a user (filtered by company) and choose a role, disabling `user` on edit.
  - Implemented generic view classes `ProjectCompanyUserRoleAllocateView`, `ProjectCompanyUserRoleUpdateView`, and `ProjectCompanyUserRoleRemoveView`.
  - Created templates for role assignment and deletion confirmation.
- Verification command:
  - `.venv\Scripts\python.exe manage.py check`
- Result: PASS

---

### Step 5: Map Stakeholder Role URL Routes
- Files changed:
  - [NEW] [stakeholder_role_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/urls/stakeholder_role_urls.py)
  - [MODIFY] [__init__.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/urls/__init__.py)
- What changed:
  - Created url routes mapping allocation, update, and deletion views for stakeholder roles.
  - Registered `stakeholder-role/` under the main Consultant app URL inclusion file.
- Verification command:
  - `.venv\Scripts\python.exe manage.py check`
- Result: PASS

---

### Step 6: Update UI Templates on Project Setup
- Files changed:
  - [MODIFY] [project_setup.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/project_setup.html)
- What changed:
  - Updated Client, Contractor, and Consultant cards to loop over `project.project_company_user_roles.all`.
  - Listed assigned users' names, emails, and roles inside each section.
  - Linked to allocation, edit role, and delete role views under each card.
- Verification command:
  - `.venv\Scripts\python.exe manage.py check`
- Result: PASS

---

### Step 7: Implement Permission Check Mixin and Guard Views
- Files changed:
  - [MODIFY] [permissions.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/core/Utilities/permissions.py)
- What changed:
  - Implemented `UserHasStakeholderRoleGenericMixin` to allow validating that a user has one of specific stakeholder roles (Admin, Supervisor, Capturer) for a given project/company context.
- Verification command:
  - `.venv\Scripts\python.exe manage.py check`
- Result: PASS

---

### Step 8: Add Integration and View Tests
- Files changed:
  - [NEW] [test_stakeholder_role_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/tests/test_stakeholder_role_views.py)
  - [MODIFY] [stakeholder_role_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/stakeholder_role_views.py)
- What changed:
  - Wrote 7 comprehensive integration test cases validating GET, POST, validation error handling, role updating, assignment deletion, and user permissions checking.
  - Refactored `form_valid` in `ProjectCompanyUserRoleAllocateView` to check unique constraints before saving to prevent transaction-level rollback errors.
- Verification command:
  - `.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_stakeholder_role_views.py -v`
- Result: PASS

---

### Step 1 (Column Reordering): Update SVG icon attributes in report config template
- **Files**: [report_config.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/report_config.html)
- **Change**: Added explicit `width="16"`, `height="16"`, and `stroke-width="2"` to the Up/Down SVG buttons inside `renderColumns()`.
- **Verification**: Verified code changes successfully modified.
- **Result**: PASS

---

### Step 2 (Column Reordering): Enhance UX styling and button tooltips
- **Files**: [report_config.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/report_config.html)
- **Change**: Added `title="Move Up"` / `title="Move Down"` tooltips and `hover:bg-gray-100 rounded-md` styles to the Up/Down button HTML templates.
- **Verification**: Verified markup changes are present in template.
- **Result**: PASS

---

### Step 3 (Column Reordering): Verify and expand unit test coverage
- **Files**: [test_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_views.py)
- **Change**: Expanded `test_save_report_config_success` to assert that custom column reordering is saved correctly and that `get_column_config()` returns the columns in the correct custom order.
- **Verification**: Run pytest `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -v`.
- **Result**: PASS










