# Design Specification: Restrict Clients and Users by Creator

This document specifies the design to prevent non-superuser accounts from viewing or selecting clients (companies) and users (accounts) they did not create.

## Goals
1. **Creator Ownership**: Add `created_by` relationship fields to `Company` and `Account` models to trace who created them.
2. **Access Restrictions**: Restrict listings, detail views, and edit views to only show clients and users created by the logged-in user (unless they are a superuser).
3. **Form Selection Restrictions**: Filter querysets in forms and project filters to only expose clients and users created by the logged-in user.

---

## Proposed Changes

### 1. Model Updates & Migrations
* **File**: `app/Project/company/company_models.py`
  - Add `created_by` field to `Company` model referencing `Account`.
* **File**: `app/Account/models.py`
  - Add `created_by` field to `Account` model referencing `self`.
* Generate and run migrations:
  - `.venv\Scripts\python.exe manage.py makemigrations`
  - `.venv\Scripts\python.exe manage.py migrate`

### 2. Populate `created_by` on Creation
* **File**: `app/Consultant/views/client_management_views.py`
  - In `ClientCreateView.form_valid()`, assign `form.instance.created_by = self.request.user`.
* **File**: `app/Consultant/views/consultant_views.py`
  - In `ClientInviteUserView.post()`, assign `created_by=request.user` when invoking `Account.objects.create_user`.
* **File**: `app/Consultant/views/stakeholder_role_views.py`
  - In `CompanyInviteUserView.form_valid()`, assign `created_by=self.request.user` when invoking `Account.objects.create_user`.
* **File**: `app/core/dynamic_quick_create.py`
  - In `QuickCreateSubmitView.post()`, assign `instance.created_by = request.user` if the model has a `created_by` field.

### 3. View & Mixin-Level QuerySet Filtering
* **File**: `app/Consultant/views/mixins.py`
  - In `ClientMixin.get_queryset()`, restrict `Company` query to `created_by=self.request.user` for non-superusers.
  - In `ConsultantMixin.get_clients()`, restrict `Company` query to `created_by=self.request.user` for non-superusers.
* **File**: `app/Consultant/views/consultant_views.py`
  - In `ClientUserListView.get()`, `ClientInviteUserView.get()`, `ClientInviteUserView.post()`, `ClientRemoveUserView.post()`, and `ClientResendInviteView.post()`, check if the client's `created_by` matches the logged-in user (raise `Http404` if not).
  - In `ClientUserListView.get()`, filter `client.users.all()` by `created_by=request.user` for non-superusers.

### 4. Form & Filter Field Filtering
* **File**: `app/Consultant/forms.py`
  - In `ProjectClientForm.__init__()`, restrict choice list to `created_by=user` for non-superusers.
* **File**: `app/Project/projects/project_forms.py`
  - In `ProjectFilterForm.__init__()`, filter `client_queryset` by `created_by=user` for non-superusers.
* **File**: `app/Project/forms/forms.py`
  - Update `ClientForm.__init__()` and pass `user=self.request.user` to filter the user/consultant selections.

---

## Verification Plan
* Add unit tests in `app/Consultant/tests/test_demo_tier_consultant.py` and `app/Project/tests/test_demo_companies.py` verifying client list, user list, and forms filter items based on the creator.
