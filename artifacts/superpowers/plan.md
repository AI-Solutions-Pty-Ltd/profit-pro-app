# Implementation Plan - Setup Page Redirects for Client and Contractor Allocation

## Goal
To automatically navigate the user back to the **Project Setup** dashboard page (`project:project-setup`) upon successfully allocating or removing a Client or Contractor company, instead of redirecting them to the intermediate company list pages.

---

## Assumptions
- The target environment is a Django application running on Python 3.13+ (or Python 3.11+).
- The `project:project-setup` URL pattern exists, takes a `pk` parameter representing the project primary key, and resolves to the setup dashboard.
- Modifying redirects requires updating `get_success_url` in `FormView`s and `redirect` in simple POST view handlers, plus updating any affected unit tests.

---

## Plan

### Step 1: Update client allocation and removal views
* **Files**:
  - [MODIFY] [project_client_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/project_client_views.py)
* **Change**:
  - Update `ProjectAllocateExistingClientView.get_success_url` to return `project:project-setup` with project `pk`:
    ```python
    def get_success_url(self):
        """Redirect to project setup page."""
        return reverse_lazy(
            "project:project-setup",
            kwargs={"pk": self.project.pk},
        )
    ```
  - Update `ProjectClientRemoveView.post` to redirect to `project:project-setup` with project `pk`:
    ```python
    return redirect(
        "project:project-setup", pk=self.project.pk
    )
    ```
* **Verify**:
  - Run syntax validation: `.venv\Scripts\python.exe -m ruff check app/Consultant/views/project_client_views.py`

### Step 2: Update contractor allocation and removal views
* **Files**:
  - [MODIFY] [project_contractor_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/views/project_contractor_views.py)
* **Change**:
  - Update `ProjectAllocateExistingContractorView.get_success_url` to return `project:project-setup` with project `pk`:
    ```python
    def get_success_url(self):
        """Redirect to project setup page."""
        return reverse_lazy(
            "project:project-setup",
            kwargs={"pk": self.project.pk},
        )
    ```
  - Update `ProjectContractorRemoveView.post` to redirect to `project:project-setup` with project `pk`:
    ```python
    return redirect(
        "project:project-setup", pk=self.project.pk
    )
    ```
* **Verify**:
  - Run syntax validation: `.venv\Scripts\python.exe -m ruff check app/Consultant/views/project_contractor_views.py`

### Step 3: Update and expand unit test suites
* **Files**:
  - [MODIFY] [test_contractor_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Consultant/tests/test_contractor_views.py)
* **Change**:
  - In `TestProjectContractorRemoveView.test_post_remove_contractor_from_project`, update the expected redirect assertion from `client:contractor-management:contractor-list` to `project:project-setup`:
    ```python
    setup_url = reverse(
        "project:project-setup",
        kwargs={"pk": self.project.pk},
    )
    self.assertRedirects(response, setup_url)
    ```
* **Verify**:
  - Run the test suite: `.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_contractor_views.py -v`

### Step 4: Run all related tests and finalize
* **Files**: None
* **Change**:
  - Run the full Consultant and forms test suites to ensure that all redirections and queryset filters work together perfectly.
  - Run `graphify update .` to keep the AST graph in sync.
* **Verify**:
  - Run command: `.venv\Scripts\python.exe -m pytest app/Consultant/tests app/Project/tests -v`
  - Rebuild AST graph: `graphify update .`

---

## Risks & mitigations
- **Risk**: Test failures in views that expect redirects to company lists.
  - *Mitigation*: We identified the single test case `test_post_remove_contractor_from_project` in `test_contractor_views.py` that makes this assertion, and will update it as part of our plan.

---

## Rollback plan
- To rollback changes:
  - Revert view modifications in `project_client_views.py` and `project_contractor_views.py` to their previous redirection URLs.
  - Revert `test_post_remove_contractor_from_project` in `test_contractor_views.py`.
