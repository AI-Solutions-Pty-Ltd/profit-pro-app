# Superpowers Brainstorm - Setup Page Redirects for Client and Contractor Allocation

This document outlines the goal, context, risks, and implementation strategies for redirecting the user to the project setup page upon completing client or contractor allocation or removal.

---

## Goal
To enhance the user experience by automatically navigating the user back to the **Project Setup** dashboard page (`project:project-setup`) immediately after they successfully allocate or remove a Client or Contractor company, instead of redirecting them to the intermediate company lists.

---

## Constraints
- **Redirection Patterns**: Django FormViews use `get_success_url` with lazy resolution, whereas normal HTTP POST views use `redirect()`.
- **URL Parameters**: The setup page URL `project:project-setup` takes keyword parameter `pk` (representing the project ID), whereas the previous lists took `project_pk`.
- **Unit Test Integrity**: Any views and redirect checks in unit tests must be aligned with the new redirection destinations.

---

## Known context
- **Client Allocation**:
  - View class: `ProjectAllocateExistingClientView` in `app/Consultant/views/project_client_views.py`
  - Current redirect: `client:client-management:client-list`
- **Client Removal**:
  - View class: `ProjectClientRemoveView` in `app/Consultant/views/project_client_views.py`
  - Current redirect: `client:client-management:client-list`
- **Contractor Allocation**:
  - View class: `ProjectAllocateExistingContractorView` in `app/Consultant/views/project_contractor_views.py`
  - Current redirect: `client:contractor-management:contractor-list`
- **Contractor Removal**:
  - View class: `ProjectContractorRemoveView` in `app/Consultant/views/project_contractor_views.py`
  - Current redirect: `client:contractor-management:contractor-list`

---

## Risks
- **Broken View Tests**: Tests checking HTTP post redirects in `test_client_views.py` and `test_contractor_views.py` might expect redirects to list views instead of the setup page.
  - *Mitigation*: Identify and update the corresponding assertions in the test suites.

---

## Options

### Option 1: Direct View Redirection (Recommended)
Touch individual `get_success_url` methods and `redirect()` statements in the target views to point directly to `project:project-setup`.
- **Pros**: Clear, robust, standard Django pattern.
- **Cons**: Requires touching 4 view methods.

### Option 2: Dynamic Query Parameter Redirection
Allow a dynamic `next` parameter in request query strings to control redirects.
- **Pros**: Highly flexible for generic views.
- **Cons**: Adds unnecessary complexity when the desired workflow is fixed.

---

## Recommendation
Implement **Option 1**. Explicitly update the redirects in `project_client_views.py` and `project_contractor_views.py` to point directly to `project:project-setup` using `self.project.pk` (or `self.project.pk`).

---

## Acceptance criteria
1. Successfully allocating a client to a project redirects the user to the project setup dashboard page (`/project/<pk>/setup/` or similar).
2. Successfully removing a client from a project redirects the user to the project setup dashboard page.
3. Successfully allocating a contractor redirects the user to the project setup dashboard page.
4. Successfully removing a contractor redirects the user to the project setup dashboard page.
5. All related tests in `app/Consultant/tests/` verify these new redirect locations.
