# Design Doc: Move Sectors, Areas, Disciplines, Project Stages to System Library

## Goal
The goal of this task is to move the global project classification categories (Sectors, Areas, Disciplines, and Project Stages) out of the general "Project Management" tab structure and relocate them into the staff-only "System Library" module (managed under the `Estimator` app).

## Background Context
Currently, these four categories are managed via tabs on the `project_list` page (under the `/project/` route namespace) and are accessible to regular contractors/consultants.
Since these represent master global reference data that gets cloned into individual projects, they belong in the **System Library**, restricted strictly to staff/admin users.

## Proposed Design

### 1. View & Permission Restructure
All category views will be modified to require staff privileges using a local `SystemLibraryMixin` to prevent circular import issues.
* **Views Modified**:
  - `app/Project/categories/category_views.py` (Sectors)
  - `app/Project/categories/subcategory_views.py` (Areas)
  - `app/Project/categories/discipline_views.py` (Disciplines)
  - `app/Project/categories/stage_views.py` (Project Stages)

* **Permission Mixin**:
  ```python
  from django.contrib.auth.mixins import UserPassesTestMixin
  from django.views.generic.base import ContextMixin

  class SystemLibraryMixin(UserPassesTestMixin, ContextMixin):
      """Mixin for system library views: requires staff."""
      def test_func(self):
          return self.request.user.is_authenticated and self.request.user.is_staff

      def get_context_data(self, **kwargs):
          context = super().get_context_data(**kwargs)
          context["is_system_view"] = True
          return context
  ```

### 2. URL Namespace Relocation
* **Removed from Project namespace** (`app/Project/urls/__init__.py`):
  - `/project/project-categories/`
  - `/project/project-subcategories/`
  - `/project/project-discipline/`
  - `/project/project-stage/`
* **Added to Estimator namespace** (`app/Estimator/urls.py`):
  - `/estimator/system/sectors/` -> `sys_sectors`
  - `/estimator/system/areas/` -> `sys_areas`
  - `/estimator/system/disciplines/` -> `sys_disciplines`
  - `/estimator/system/project-stages/` -> `sys_project_stages`
  - Respective sub-routes for create, update, and delete.

### 3. Template Updates
We will move the template files from `app/Project/templates/categories/` to `app/Estimator/templates/estimator/system/` and rename them appropriately:
* `category_manage.html` -> `sector_manage.html` (along with `sector_form.html` & `sector_confirm_delete.html`)
* `subcategory_manage.html` -> `area_manage.html` (along with `area_form.html` & `area_confirm_delete.html`)
* `discipline_manage.html` -> `discipline_manage.html` (along with `discipline_form.html` & `discipline_confirm_delete.html`)
* `stage_manage.html` -> `stage_manage.html` (along with `stage_form.html` & `stage_confirm_delete.html`)

These templates will be updated to:
* Extend `estimator/system/base_system.html`.
* Use the `sub_content` block.
* Reference the new `estimator:sys_*` URL namespace.

### 4. Layout Updates
* **System Library Layout (`base_system.html`)**:
  - Add Sectors, Areas, Disciplines, and Project Stages navigation links to the tabs header.
* **Project List Layout (`project_list.html`)**:
  - Remove the tab structure, leaving the list page to focus entirely on project records.
