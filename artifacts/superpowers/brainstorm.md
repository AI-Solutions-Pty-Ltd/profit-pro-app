# Superpowers Brainstorm: Stakeholder User & Role Management

## Goal
Refactor and improve user management inside the stakeholder submodules (Client Management, Contractor Management, and Consultant Management). The feature must allow assigning users and associating specific roles (Admin, Supervisor, and Capturer) to these submodules (contextualized by project and stakeholder company).

## Constraints
1. **Roles defined**: Must support exactly three stakeholder roles: Admin, Supervisor, and Capturer.
2. **Contextual Scope**: Roles must be assigned per stakeholder company per project (e.g., a user might be a Capturer for Contractor A on Project X, but a Supervisor on Project Y).
3. **No security regression**: Must respect existing tenant/permission isolation.
4. **Integration**: Must fit into the existing Django app structure, particularly integrating with the views in [views](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views) where client, contractor, and consultant management is defined.
5. **No hard-coded values where configurable**: Follow established project conventions for models (inheriting from `BaseModel`, using factories, and testing first).

## Known context
1. **Current Models**:
   * [Company](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/company/company_models.py#L26) represents the stakeholder companies with `Type` choices (Client, Contractor, Lead Consultant, Consultant).
   * [Account](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/models.py#L101) represents the users.
   * [Project](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/projects_models.py#L42) connects users and companies via `users`, `contractors`, `quantity_surveyors`, `lead_consultants`, `consultants`, etc.
   * [ProjectRole](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/models/project_roles_models.py#L81) maps general project roles to individual users on a project level, using choices in `Role`.
2. **Current Views**:
   * Stakeholder management views are defined in `app/Consultant/views/`:
     * [client_management_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/client_management_views.py)
     * [contractor_management_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/contractor_management_views.py)
     * [lead_consultant_management_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/lead_consultant_management_views.py)
   * The visual cards for managing these stakeholder assignments are located in [project_setup.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/project_setup.html#L532).

## Risks
1. **Role Clashes**: Confusing general project-level roles (like `Admin`, `User`) with submodule-specific stakeholder roles (like `Contractor Admin`, `Client Supervisor`).
   * *Mitigation*: Clearly separate these concepts in both the database (either via separate relationship models or distinct role namespaces) and the UI.
2. **Permission Bypass**: A stakeholder capturer might find a way to perform supervisor/admin tasks if view permissions are not properly guarded by the new roles.
   * *Mitigation*: Implement custom class-based view mixins or helper decorators that explicitly check the user's stakeholder role context on the project.
3. **Data Migration Complexity**: Modifying existing relationships to accommodate roles might break existing project-stakeholder mappings.
   * *Mitigation*: Keep existing direct ManyToMany associations as fallback or baseline access, and overlay the role mappings dynamically, or create clean migration scripts that initialize existing project users as "Admin" or "Supervisor" by default.

## Options (2???4)

### Option 1: Submodule-Specific Stakeholder Role Model (Recommended)
Create a new model `ProjectCompanyUserRole` that acts as a formal link between `Project`, `Company`, `Account`, and a new choice field `role` (choices: Admin, Supervisor, Capturer).
* **Pros**:
  * Extremely clean and modular. Doesn't pollute the general `ProjectRole` model.
  * Fully supports project-specific and company-specific role scoping.
  * Straightforward to build dedicated UI forms for adding/editing users and their roles under each stakeholder card.
* **Cons**:
  * Requires creating a new table and migrating the database.

### Option 2: Expand `ProjectRole` with a Foreign Key to `Company`
Add a nullable `company` ForeignKey field to the existing `ProjectRole` model. Add new role choices to `Role` (e.g., `STAKEHOLDER_ADMIN`, `STAKEHOLDER_SUPERVISOR`, `STAKEHOLDER_CAPTURER`).
* **Pros**:
  * Reuses the existing `ProjectRole` model structure and permission checkers.
  * Fewer new tables in the database.
* **Cons**:
  * Pollutes the general `Role` choices with sub-module specific roles.
  * Can lead to validation complexity (e.g., ensuring a regular `Admin` role does not have a `company` assigned, whereas a `STAKEHOLDER_ADMIN` must have a `company` assigned).

### Option 3: Use Django's ManyToMany `through` Model on `Company.users`
Change `Company.users` relation to use a custom `through` model `CompanyUser` containing a `role` field.
* **Pros**:
  * Directly embeds roles into the relationship between companies and users.
* **Cons**:
  * Roles would be global to the company, not specific to a project. A user would have the same role (e.g., Capturer) for a Contractor company across all projects, which lacks the project-level flexibility that is usually required.
  * Rewriting an existing simple ManyToMany field to use a `through` model is historically error-prone and complex in Django migrations.

## Recommendation
We recommend **Option 1**. It is the most robust and clean design pattern for stakeholder role context. It avoids polluting general project roles and ensures that a user can have different roles under different projects for the same stakeholder company.

## Acceptance criteria
1. Introduce a new model `ProjectCompanyUserRole` inheriting from `BaseModel`. It must link:
   * `project` (ForeignKey to `Project`)
   * `company` (ForeignKey to `Company`)
   * `user` (ForeignKey to `Account`)
   * `role` (CharField with choices: Admin, Supervisor, Capturer)
2. Define a database unique constraint on `(project, company, user)` to prevent duplicate assignments of the same user under the same company and project.
3. Update [project_setup.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/project_setup.html) to display the assigned users and their roles under the respective Client, Contractor, and Consultant management cards.
4. Refactor client, contractor, and consultant allocation views to support adding/updating users and their specific roles.
5. Implement permission checking decorators or mixins (e.g., `UserHasStakeholderRoleMixin`) to guard actions (e.g., only Admin/Supervisor can certify payments, while Capturers can only save drafts).
6. Create model factories and comprehensive pytest test cases for the new model and views.

