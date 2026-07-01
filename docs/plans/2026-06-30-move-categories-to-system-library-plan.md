# Move Sectors, Areas, Disciplines, Project Stages to System Library Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Move project classification categories (Sectors, Areas, Disciplines, Project Stages) to the staff-only System Library module.

**Architecture:** Relocate views/URLs/templates to System Library namespace (`estimator` app) and restrict them using `SystemLibraryMixin`.

**Tech Stack:** Python, Django, Pytest, Tailwind CSS

---

### Task 1: Write failing tests for System Library category views

**Files:**
- Create: `app/Project/tests/test_system_categories.py`

**Step 1: Write the failing test**
Create a test file to verify that accessing the new system library URLs requires staff/admin permissions and old URLs are removed (404).

```python
"""Tests for global category management moved to System Library."""

import pytest
from django.urls import reverse, NoReverseMatch

from app.Account.tests.factories import AccountFactory

@pytest.mark.django_db
class TestSystemCategoriesAccess:
    """Test access control for System Library category views."""

    def setup_method(self):
        self.staff_user = AccountFactory(is_staff=True)
        self.regular_user = AccountFactory(is_staff=False)
        self.system_urls = [
            ("estimator:sys_sectors", "estimator:sys_sector_create"),
            ("estimator:sys_areas", "estimator:sys_area_create"),
            ("estimator:sys_disciplines", "estimator:sys_discipline_create"),
            ("estimator:sys_project_stages", "estimator:sys_project_stage_create"),
        ]

    def test_new_urls_resolving_and_staff_access(self, client):
        """Verify new URLs exist and are accessible only to staff."""
        client.force_login(self.staff_user)
        for list_url_name, _ in self.system_urls:
            url = reverse(list_url_name)
            response = client.get(url)
            # Should render successfully
            assert response.status_code == 200

    def test_new_urls_deny_regular_user(self, client):
        """Verify non-staff users are denied access to the new URLs."""
        client.force_login(self.regular_user)
        for list_url_name, _ in self.system_urls:
            url = reverse(list_url_name)
            response = client.get(url)
            # Django's UserPassesTestMixin redirects non-staff or returns 403
            assert response.status_code in [302, 403]

    def test_old_urls_no_longer_resolve(self):
        """Verify old URL namespace elements no longer resolve."""
        old_names = [
            "project:category-list",
            "project:subcategory-list",
            "project:discipline-list",
            "project:project-stage-list",
        ]
        for name in old_names:
            with pytest.raises(NoReverseMatch):
                reverse(name)
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_system_categories.py -v`
Expected: FAIL with `NoReverseMatch` since the new URLs are not yet defined.

**Step 3: Commit**
```bash
git add app/Project/tests/test_system_categories.py
git commit -m "test: add failing tests for System Library category views"
```

---

### Task 2: Implement SystemLibraryMixin in category view files

**Files:**
- Modify: `app/Project/categories/category_views.py`
- Modify: `app/Project/categories/subcategory_views.py`
- Modify: `app/Project/categories/discipline_views.py`
- Modify: `app/Project/categories/stage_views.py`

**Step 1: Update views implementation**
In each of the views files:
1. Define/import `SystemLibraryMixin`:
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
2. Replace `UserHasGroupGenericMixin` with `SystemLibraryMixin` in all view classes.
3. Update `template_name` paths to the new location under `estimator/system/`:
   - `category_views.py`: `estimator/system/sector_manage.html` (create/update point to `estimator/system/sector_form.html`, delete points to `estimator/system/sector_confirm_delete.html`)
   - `subcategory_views.py`: `estimator/system/area_manage.html`, `estimator/system/area_form.html`, `estimator/system/area_confirm_delete.html`
   - `discipline_views.py`: `estimator/system/discipline_manage.html`, `estimator/system/discipline_form.html`, `estimator/system/discipline_confirm_delete.html`
   - `stage_views.py`: `estimator/system/stage_manage.html`, `estimator/system/stage_form.html`, `estimator/system/stage_confirm_delete.html`
4. Update `success_url` redirects/reverses to use `estimator:sys_sectors`, `estimator:sys_areas`, `estimator:sys_disciplines`, `estimator:sys_project_stages`.
5. Remove `get_breadcrumbs` methods (System views do not use breadcrumbs).

**Step 2: Commit**
```bash
git add app/Project/categories/*.py
git commit -m "feat: migrate views to SystemLibraryMixin and update target templates"
```

---

### Task 3: Relocate URL routing

**Files:**
- Modify: `app/Project/urls/__init__.py`
- Modify: `app/Estimator/urls.py`

**Step 1: Update URL patterns**
1. Remove category URL inclusions from `app/Project/urls/__init__.py` (both imports and patterns under `urlpatterns` for `project-categories/`, `project-subcategories/`, `project-discipline/`, `project-stage/`).
2. Add new System Library URLs to `app/Estimator/urls.py` under the `# ── System Library ──` header:
   ```python
   # System Sectors
   path(
       "system/sectors/",
       category_views.ProjectCategoryListView.as_view(),
       name="sys_sectors",
   ),
   path(
       "system/sectors/create/",
       category_views.ProjectCategoryCreateView.as_view(),
       name="sys_sector_create",
   ),
   path(
       "system/sectors/<int:pk>/update/",
       category_views.ProjectCategoryUpdateView.as_view(),
       name="sys_sector_update",
   ),
   path(
       "system/sectors/<int:pk>/delete/",
       category_views.ProjectCategoryDeleteView.as_view(),
       name="sys_sector_delete",
   ),

   # System Areas
   path(
       "system/areas/",
       subcategory_views.ProjectSubCategoryListView.as_view(),
       name="sys_areas",
   ),
   path(
       "system/areas/create/",
       subcategory_views.ProjectSubCategoryCreateView.as_view(),
       name="sys_area_create",
   ),
   path(
       "system/areas/<int:pk>/update/",
       subcategory_views.ProjectSubCategoryUpdateView.as_view(),
       name="sys_area_update",
   ),
   path(
       "system/areas/<int:pk>/delete/",
       subcategory_views.ProjectSubCategoryDeleteView.as_view(),
       name="sys_area_delete",
   ),

   # System Disciplines
   path(
       "system/disciplines/",
       discipline_views.ProjectDisciplineListView.as_view(),
       name="sys_disciplines",
   ),
   path(
       "system/disciplines/create/",
       discipline_views.ProjectDisciplineCreateView.as_view(),
       name="sys_discipline_create",
   ),
   path(
       "system/disciplines/<int:pk>/update/",
       discipline_views.ProjectDisciplineUpdateView.as_view(),
       name="sys_discipline_update",
   ),
   path(
       "system/disciplines/<int:pk>/delete/",
       discipline_views.ProjectDisciplineDeleteView.as_view(),
       name="sys_discipline_delete",
   ),

   # System Project Stages
   path(
       "system/project-stages/",
       stage_views.ProjectStageListView.as_view(),
       name="sys_project_stages",
   ),
   path(
       "system/project-stages/create/",
       stage_views.ProjectStageCreateView.as_view(),
       name="sys_project_stage_create",
   ),
   path(
       "system/project-stages/<int:pk>/update/",
       stage_views.ProjectStageUpdateView.as_view(),
       name="sys_project_stage_update",
   ),
   path(
       "system/project-stages/<int:pk>/delete/",
       stage_views.ProjectStageDeleteView.as_view(),
       name="sys_project_stage_delete",
   ),
   ```

**Step 2: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_system_categories.py -v`
Expected: PASS

**Step 3: Commit**
```bash
git add app/Project/urls/__init__.py app/Estimator/urls.py
git commit -m "feat: re-route category URLs to Estimator system namespace"
```

---

### Task 4: Move and update Template Files

**Files:**
- Create/Move: `app/Estimator/templates/estimator/system/` (relocated category pages)
- Delete: `app/Project/templates/categories/`

**Step 1: Move and rename templates**
1. Move and rename the manage pages to their new names in `app/Estimator/templates/estimator/system/`:
   - `category_manage.html` -> `sector_manage.html`
   - `subcategory_manage.html` -> `area_manage.html`
   - `discipline_manage.html` -> `discipline_manage.html`
   - `stage_manage.html` -> `stage_manage.html`
2. Move and rename the support form and delete confirmation templates:
   - `subcategory_form.html` -> `area_form.html`
   - `subcategory_confirm_delete.html` -> `area_confirm_delete.html`
   - `discipline_form.html` -> `discipline_form.html`
   - `discipline_confirm_delete.html` -> `discipline_confirm_delete.html`
   - `stage_form.html` -> `stage_form.html`
   - `stage_confirm_delete.html` -> `stage_confirm_delete.html`
3. Create `sector_form.html` and `sector_confirm_delete.html` (replicating the layout from `discipline` files but adapted to sectors/categories) to ensure completeness.

**Step 2: Update Layouts & URLs in Templates**
In each `*_manage.html` file:
1. Change `{% extends "base_full.html" %}` to `{% extends "estimator/system/base_system.html" %}`.
2. Change `{% block content %}` to `{% block sub_content %}`.
3. Remove the local tabs navigation block.
4. Replace JS form URLs from `/project/project-*` to `/estimator/system/*` (e.g. `/estimator/system/sectors/`).
5. Replace template URL references (like form action `{% url 'project:category-create' %}`) with `{% url 'estimator:sys_sector_create' %}`.

In each `*_form.html` and `*_confirm_delete.html` file:
1. Change inheritance to `estimator/system/base_system.html`.
2. Change block to `sub_content`.
3. Update reverse URL references (e.g., pointing back to `estimator:sys_sectors`).

**Step 3: Commit**
```bash
git add app/Estimator/templates/estimator/system/
git commit -m "feat: move category templates to estimator system library and update layouts"
```

---

### Task 5: Add Tabs to base_system.html

**Files:**
- Modify: `app/Estimator/templates/estimator/system/base_system.html`

**Step 1: Add new tabs**
Add the four new tabs in the navigation bar of `base_system.html` using the new `estimator` namespace:
```html
                        <a href="{% url 'estimator:sys_sectors' %}"
                           class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm {% if url_name == 'sys_sectors' or url_name == 'sys_sector_upload' %}border-indigo-500 text-indigo-600{% else %}border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300{% endif %}">
                            {% heroicon_outline "tag" class="inline-block mr-1 w-4 h-4" %}
                            Sectors
                        </a>
                        <a href="{% url 'estimator:sys_areas' %}"
                           class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm {% if url_name == 'sys_areas' or url_name == 'sys_area_upload' %}border-indigo-500 text-indigo-600{% else %}border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300{% endif %}">
                            {% heroicon_outline "tag" class="inline-block mr-1 w-4 h-4" %}
                            Areas
                        </a>
                        <a href="{% url 'estimator:sys_disciplines' %}"
                           class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm {% if url_name == 'sys_disciplines' or url_name == 'sys_discipline_upload' %}border-indigo-500 text-indigo-600{% else %}border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300{% endif %}">
                            {% heroicon_outline "academic-cap" class="inline-block mr-1 w-4 h-4" %}
                            Disciplines
                        </a>
                        <a href="{% url 'estimator:sys_project_stages' %}"
                           class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm {% if url_name == 'sys_project_stages' or url_name == 'sys_project_stage_upload' %}border-indigo-500 text-indigo-600{% else %}border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300{% endif %}">
                            {% heroicon_outline "tag" class="inline-block mr-1 w-4 h-4" %}
                            Project Stages
                        </a>
```

**Step 2: Commit**
```bash
git add app/Estimator/templates/estimator/system/base_system.html
git commit -m "feat: add Sectors, Areas, Disciplines, and Project Stages tabs to System Library nav"
```

---

### Task 6: Remove Old Tabs from project_list.html

**Files:**
- Modify: `app/Project/templates/project/project_list.html`

**Step 1: Simplify project list layout**
Remove the tabs navigation bar (`<!-- Tabs -->` and its containing elements) from `project_list.html` entirely to focus the view on project management only.

**Step 2: Run all tests to verify**
Run: `.venv\Scripts\python.exe -m pytest`
Verify all project and category-related tests compile and pass.

**Step 3: Commit**
```bash
git add app/Project/templates/project/project_list.html
git commit -m "style: remove redundant category tabs from project list template"
```
