# Superpowers Plan: Refactor Consultants to Support Multiple Consultants

## Goal
Refactor consultants in the application to support assigning multiple consultant companies to a project, separating them into Lead Consultants and regular Consultants.

## Assumptions
- Virtual environment `.venv` exists and contains all required django/pytest packages.
- Pytest is used for testing.
- The project has existing migrations that we can append to.

## Plan

### 1. Extend Company Type Choices
- **Files**: [company_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/company/company_models.py)
- **Change**: Add `CONSULTANT = "CONSULTANT", "Consultant"` to the `Company.Type` choices.
- **Verify**: Inspect the file and run a quick python shell verification:
  ```bash
  .venv\Scripts\python.exe -c "from app.Project.models import Company; print(Company.Type.CONSULTANT)"
  ```

### 2. Add Many-to-Many Field to Project Model
- **Files**: [projects_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/projects_models.py)
- **Change**: 
  - Add `consultants` ManyToManyField to `Project` model (pointing to `Company`).
  - Add a `@property` for `lead_consultant` returning the first company of type `LEAD_CONSULTANT` for backwards compatibility.
  - Temporarily keep the `lead_consultant` ForeignKey field in the DB to write a data migration.
- **Verify**: Run `makemigrations` to generate schema changes.

### 3. Data Migration and ForeignKey Removal
- **Files**: [projects_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/projects_models.py), migration files
- **Change**: 
  - Create a migration to add the ManyToMany relationship.
  - Write a data migration script to copy existing `lead_consultant_id` values for all projects to the new ManyToMany relation.
  - Remove `lead_consultant` ForeignKey from the `Project` model.
  - Generate the final schema migration to drop the old `lead_consultant` ForeignKey column.
- **Verify**: Run `.venv\Scripts\python.exe manage.py migrate` to apply all migrations and verify no errors.

### 4. Update Forms
- **Files**: [forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/forms/forms.py)
- **Change**:
  - Update `ProjectLeadConsultantForm` to work with ManyToMany (allowing selection of lead consultants).
  - Create a new `ProjectConsultantForm` for assigning regular consultants.
  - Update `LeadConsultantQuickCreateForm` if necessary to handle the type properly.
- **Verify**: Verify forms validate and return correct querysets.

### 5. Update Views and URLs
- **Files**: 
  - [project_lead_consultant_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/project_lead_consultant_views.py)
  - [project_lead_consultant_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/urls/project_lead_consultant_urls.py)
  - [lead_consultant_management_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/lead_consultant_management_views.py)
- **Change**:
  - Update `ProjectAllocateLeadConsultantView` and `ProjectLeadConsultantRemoveView` to add/remove to `project.consultants` instead of setting `project.lead_consultant`.
  - Add new views `ProjectAllocateConsultantView` and `ProjectConsultantRemoveView` for regular consultants.
  - Update management list, create, and update views to support both `LEAD_CONSULTANT` and `CONSULTANT` types.
  - Add URL patterns for regular consultant allocation and removal.
- **Verify**: Check URL routing and ensure no view crashes.

### 6. Update Templates
- **Files**:
  - [project_setup.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/project_setup.html)
  - [lead_consultant_list.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/lead_consultant/lead_consultant_list.html)
  - [allocate_lead_consultant_form.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/templates/lead_consultant/allocate_lead_consultant_form.html)
- **Change**:
  - Update `project_setup.html`'s "Consultant Management" card to display all assigned Lead Consultants and Consultants, along with the two allocation buttons (`+ Assign Lead Consultant` and `+ Assign Consultant`) and remove links for each company.
  - Update `lead_consultant_list.html` to manage both lead and regular consultant companies.
- **Verify**: Load the project setup page and verify correct UI rendering.

### 7. Update and Run Tests
- **Files**:
  - [test_allocation_fixes.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/tests/test_allocation_fixes.py)
  - [test_lead_consultant_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/tests/test_lead_consultant_views.py)
- **Change**: Update the unit tests to mock and test ManyToMany consultant assignment and filtering.
- **Verify**: Run all tests:
  ```bash
  .venv\Scripts\python.exe -m pytest app/Consultant/tests/
  ```

## Risks & mitigations
- **Risk**: Database query failure in other modules that expect `project.lead_consultant` as an ORM relation.
  - *Mitigation*: Adding the `@property` handles direct attribute access. Any DB query filters (`lead_consultant=...`) will be refactored to query `consultants=...`.
- **Risk**: Data loss during migration.
  - *Mitigation*: The data migration will be fully tested and run before the schema column is deleted.

## Rollback plan
- Revert git changes using `git checkout -- .`.
- Roll back migration using `.venv\Scripts\python.exe manage.py migrate Project <previous_migration_name>`.

