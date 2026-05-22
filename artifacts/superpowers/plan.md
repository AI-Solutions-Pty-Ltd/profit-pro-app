# Seeding and Filtering Demo Companies for Demo Tier Users - Implementation Plan

## Goal
To search for and seed three specific companies:
1. Client: `"Demo Client"` (Type: `Company.Type.CLIENT`)
2. Contractor: `"Demo Contractor 1"` (Type: `Company.Type.CONTRACTOR`)
3. Lead Consultant: `"Demo Consultant 1"` (Type: `Company.Type.LEAD_CONSULTANT`)

If these companies do not exist in the database, they will be seeded automatically. Additionally, these companies must be conditionally exposed to users in the active **Demo Tier** subscription (`DEMO_TIER`) inside both the project setup dropdowns (Client selection, Contractor selection, Lead Consultant selection forms) and the portfolio filter dropdowns, while remaining isolated from regular users.

## Assumptions
* The target environment is a Django application running on Python 3.13+ with a `.venv` virtual environment active.
* The `Company` model in `app/Project/company/company_models.py` has enum choices for `CLIENT`, `CONTRACTOR`, and `LEAD_CONSULTANT`.
* `Account` model has properties `has_demo_permission` to identify active trial users on `DEMO_TIER`.
* All test scenarios will use `factory_boy` factories and execute through `pytest`.

---

## Plan

### Step 1: Implement `Company.ensure_demo_companies()` classmethod
* **Files**:
  * [MODIFY] [company_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/company/company_models.py)
* **Change**:
  * Add a classmethod `ensure_demo_companies()` on the `Company` model.
  * In this method, iterate over the three target demo companies and use `objects.get_or_create` to lookup/create them securely to avoid duplicates:
    * `Company(type=Company.Type.CLIENT, name="Demo Client", defaults={"registration_number": "DEMO-CLIENT"})`
    * `Company(type=Company.Type.CONTRACTOR, name="Demo Contractor 1", defaults={"registration_number": "DEMO-CONTRACTOR-1"})`
    * `Company(type=Company.Type.LEAD_CONSULTANT, name="Demo Consultant 1", defaults={"registration_number": "DEMO-CONSULTANT-1"})`
* **Verify**:
  * Run syntax validation: `.venv\Scripts\python.exe -m ruff check app/Project/company/company_models.py`

### Step 2: Hook up seeding to the `create_demo_user` management command
* **Files**:
  * [MODIFY] [create_demo_user.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/management/commands/create_demo_user.py)
* **Change**:
  * Import `Company` from `app.Project.models`.
  * In the `handle()` method of `Command`, call `Company.ensure_demo_companies()` after configuring/updating the demo user.
  * Log a success message to `self.stdout` confirming that demo companies are verified/seeded.
* **Verify**:
  * Run command to test execution: `.venv\Scripts\python.exe manage.py create_demo_user`
  * Verify the command successfully runs and prints confirmation of the seeded companies.

### Step 3: Conditionally filter querysets in project setup Forms
* **Files**:
  * [MODIFY] [forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/forms.py)
  * [MODIFY] [forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/forms/forms.py)
* **Change**:
  * In `ProjectClientForm.__init__` (`app/Consultant/forms.py`), if `user` is provided and `user.has_demo_permission` is True, update the query condition using a logical OR:
    ```python
    condition = Q(client_projects__in=projects) | Q(users=user)
    if user.has_demo_permission:
        condition |= Q(name="Demo Client")
    queryset = Company.objects.filter(
        condition,
        type=Company.Type.CLIENT,
    ).order_by("name")
    ```
  * In `ProjectContractorForm.__init__` (`app/Project/forms/forms.py`), if `user` is provided and `user.has_demo_permission` is True, update the query condition:
    ```python
    condition = Q(contractor_projects__in=projects) | Q(users=user)
    if user.has_demo_permission:
        condition |= Q(name="Demo Contractor 1")
    queryset = (
        Company.objects.filter(
            condition,
            type=Company.Type.CONTRACTOR,
        )
        .distinct()
        .order_by("name")
    )
    ```
  * In `ProjectLeadConsultantForm.__init__` (`app/Project/forms/forms.py`), if `user` is provided and `user.has_demo_permission` is True, update the query condition:
    ```python
    condition = Q(lead_consultant_projects__in=projects) | Q(users=user)
    if user.has_demo_permission:
        condition |= Q(name="Demo Consultant 1")
    queryset = (
        Company.objects.filter(
            condition,
            type=Company.Type.LEAD_CONSULTANT,
        )
        .distinct()
        .order_by("name")
    )
    ```
* **Verify**:
  * Run syntax check: `.venv\Scripts\python.exe -m ruff check app/Consultant/forms.py app/Project/forms/forms.py`

### Step 4: Include demo companies in portfolio filter dropdowns
* **Files**:
  * [MODIFY] [project_forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/project_forms.py)
* **Change**:
  * In `ProjectFilterForm.__init__` (`app/Project/projects/project_forms.py`), check if `user` is provided and `user.has_demo_permission` is True.
  * If True and `client_queryset` is not None, include the `"Demo Client"` using a union:
    ```python
    if user and user.has_demo_permission and client_queryset is not None:
        demo_clients = Company.objects.filter(type=Company.Type.CLIENT, name="Demo Client")
        client_queryset = (client_queryset | demo_clients).distinct().order_by("name")
    ```
  * If True and `contractor_queryset` is not None, include the `"Demo Contractor 1"` using a union:
    ```python
    if user and user.has_demo_permission and contractor_queryset is not None:
        demo_contractors = Company.objects.filter(type=Company.Type.CONTRACTOR, name="Demo Contractor 1")
        contractor_queryset = (contractor_queryset | demo_contractors).distinct().order_by("name")
    ```
* **Verify**:
  * Run syntax check: `.venv\Scripts\python.exe -m ruff check app/Project/projects/project_forms.py`

### Step 5: Add comprehensive pytest unit tests
* **Files**:
  * [NEW] [test_demo_companies.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_demo_companies.py)
* **Change**:
  * Write a new test suite that tests:
    * Seeding via `Company.ensure_demo_companies()` initializes exactly 3 companies with correct types and names, and calling it repeatedly does not duplicate entries.
    * An active `DEMO_TIER` user (`user.has_demo_permission == True`) can view the seeded demo companies in `ProjectClientForm`, `ProjectContractorForm`, `ProjectLeadConsultantForm`, and `ProjectFilterForm`.
    * A regular non-demo user does NOT view the seeded companies in their dropdowns or filters (unless they are explicitly associated).
    * Expired trial users on `DEMO_TIER` do NOT view the seeded companies.
* **Verify**:
  * Run the unit tests: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_demo_companies.py -v`

### Step 6: Verify and run Graphify update
* **Files**: None
* **Change**:
  * Run the entire project's pytest suite to ensure no regressions are introduced.
  * Run `graphify update .` to rebuild the codebase's knowledge graph.
* **Verify**:
  * Verify tests pass cleanly and `graphify update` executes successfully.

---

## Risks & mitigations
* **Risk**: Seeding logic duplicates companies.
  * *Mitigation*: Use `objects.get_or_create()` with both `name` and `type` inside the defaults/filters to ensure exact mapping and avoid duplicates.
* **Risk**: Performance issues with queryset union (`|`).
  * *Mitigation*: Using Django's queryset union OR-operator `|` is highly efficient on the same model. We call `.distinct().order_by("name")` immediately after to keep query execution simple.

## Rollback plan
* To rollback:
  * Remove `ensure_demo_companies` from `Company` in `app/Project/company/company_models.py`.
  * Revert query modifications in `forms.py` (both files) and `project_forms.py`.
  * Delete `app/Project/tests/test_demo_companies.py`.
  * Revert the `create_demo_user` command call to the seeding method.

---

### PERSISTENCE NOTE
Plan is stored to `artifacts/superpowers/plan.md`.
