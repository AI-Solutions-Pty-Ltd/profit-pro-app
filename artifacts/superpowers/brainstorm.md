# Superpowers Brainstorm

## Goal
To search for the following demo companies and create them if they do not exist:
* Client: `"Demo Client"` (Type: `Company.Type.CLIENT`)
* Contractor: `"Demo Contractor 1"` (Type: `Company.Type.CONTRACTOR`)
* Lead Consultant: `"Demo Consultant 1"` (Type: `Company.Type.LEAD_CONSULTANT`)

These companies must be made available to users on the **Demo Tier** subscription (`DEMO_TIER`) inside both the project setup dropdowns (Client selection, Contractor selection, Lead Consultant selection forms) and the portfolio filter dropdowns.

## Constraints
* **Virtual Environment**: Use `.venv` exclusively, prefixing execution with `.venv\Scripts\python.exe`.
* **Testing & Data**: Write new unit tests using `pytest` and `factory_boy` factories.
* **Inheritance**: Any new models or custom data models must inherit from `BaseModel`.
* **Single-Flow Execution**: Keep exactly one active task step in `docs/plans/task.md` (table-only progress tracker).
* **Graphify**: Eagerly run `graphify update .` after changes to update the project knowledge graph.

## Known Context
* `Company` model resides in `app/Project/company/company_models.py` with enum types: `CLIENT`, `CONTRACTOR`, `LEAD_CONSULTANT`.
* `create_demo_user` management command is in `app/Account/management/commands/create_demo_user.py`. It is responsible for setting up active `DEMO_TIER` accounts.
* The forms that manage project company assignments:
  * `ProjectClientForm` in `app/Consultant/forms.py` (filters clients).
  * `ProjectContractorForm` in `app/Project/forms/forms.py` (filters contractors).
  * `ProjectLeadConsultantForm` in `app/Project/forms/forms.py` (filters lead consultants).
* The dashboard filters:
  * `ProjectFilterForm` in `app/Project/projects/project_forms.py` receives querysets initialized in views like `PortfolioDashboardView` (`app/Project/views/portfolio_views.py`), `ProjectListView` (`app/Project/projects/project_views.py`), and others in `report_views.py`.
* `Account` model has `has_demo_permission` property which returns `True` if user is in active unexpired `DEMO_TIER`.

## Risks
* **Data Duplication**: Re-running the management command or seeding logic could create duplicate "Demo" companies if they are not searched by exact type and name first.
* **Scope Leakage**: Non-demo tier users must not see these demo companies in their dropdowns/filters unless the companies are explicitly assigned to their projects or accounts.
* **Test Isolation**: In testing environments, the database is clean. If tests expect these companies to exist, they must be set up via fixtures, factories, or seeded dynamically.

## Options (2–4)

### Option 1: Seed via Management Command and Helper Method, and Filter Querysets conditionally in Forms/Views (Recommended)
* **Summary**:
  1. Add a classmethod `ensure_demo_companies()` on the `Company` model that searches for and creates `"Demo Client"`, `"Demo Contractor 1"`, and `"Demo Consultant 1"` if they don't exist.
  2. Invoke `Company.ensure_demo_companies()` in the `create_demo_user` management command.
  3. In `ProjectClientForm`, `ProjectContractorForm`, and `ProjectLeadConsultantForm`, check if `user.has_demo_permission`. If so, include the corresponding demo company in the queryset.
  4. In dashboard views (e.g. `PortfolioDashboardView`, `ProjectListView`, and reports in `report_views.py`), when constructing the client/contractor querysets, check if `user.has_demo_permission`. If `True`, append/union the demo companies.
* **Pros**:
  * Decoupled and modular: seeding lives in a classmethod on `Company` and is invoked during environment setup.
  * Robust conditional filtering: only targets demo-tier users.
  * Very easy to test.
* **Cons**:
  * Requires modifying multiple dashboard views to ensure consistency of filter options.
* **Complexity / Risk**: Low.

### Option 2: Database Migration for Seeding and Filter Querysets
* **Summary**:
  * Create a standard Django data migration to seed the three demo companies.
  * Apply form and view queryset updates identically to Option 1.
* **Pros**:
  * Guaranteed to exist in all environments (including production and newly spun up instances) without needing to run a management command.
* **Cons**:
  * Slows down some fresh DB creations or test setups unless properly cached, though standard for Django.
  * Still requires the same view/form queryset modifications to make them visible to the Demo Tier.
* **Complexity / Risk**: Low.

### Option 3: Dynamic Form/View-Level Lazy Creation
* **Summary**:
  * Do not pre-seed. Instead, when the form/view is initialized, check if the demo companies exist. If not, create them dynamically during the request lifecycle.
* **Pros**:
  * Zero setup or command dependencies.
* **Cons**:
  * Major anti-pattern: writing to the database during GET requests / form instantiation.
  * Can lead to race conditions under load or concurrent users, creating duplicate companies.
* **Complexity / Risk**: High.

## Recommendation
We recommend **Option 1**. Since the environment already utilizes a standard `create_demo_user` command to configure a demo user, extending this command to seed the demo companies via a reusable classmethod `Company.ensure_demo_companies()` is clean, maintainable, and aligned with standard Django practices. We will update the forms (`ProjectClientForm`, `ProjectContractorForm`, `ProjectLeadConsultantForm`) and views (`PortfolioDashboardView`, `ProjectListView`, `ProjectReportView`, etc.) to conditionally include these companies when `user.has_demo_permission` is `True`. We will also add full unit tests for both regular and demo users using factory_boy factories.

## Acceptance Criteria
- Running `create_demo_user` seeds `"Demo Client"`, `"Demo Contractor 1"`, and `"Demo Consultant 1"` if they do not exist.
- When logged in as a user with active `DEMO_TIER` subscription (`user.has_demo_permission` is True):
  - `"Demo Client"` is available in the Client selection dropdown.
  - `"Demo Contractor 1"` is available in the Contractor selection dropdown.
  - `"Demo Consultant 1"` is available in the Lead Consultant selection dropdown.
  - All three demo companies are available in the portfolio dashboard and project list filter dropdowns.
- When logged in as a regular user (not `DEMO_TIER`):
  - These demo companies are not visible in dropdowns or filters (unless explicitly associated with their projects/accounts).
- Unit tests are added/updated to verify this behavior for both user groups.
- `ruff check .` and all `pytest` suites pass.
- `graphify update .` is executed successfully.
