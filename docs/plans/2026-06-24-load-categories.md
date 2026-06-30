# Load WBS Categories Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Add a "Load Categories" button on the scope planning page that copies the entire WBS hierarchy (Categories, SubCategories, Groups) from another project.

**Architecture:** A new Django POST API view `LoadWBSCategoriesView` will clear existing empty WBS structures and copy WBS levels from the source project. The frontend will trigger it via a select modal.

**Tech Stack:** Django, Python, HTML/JS, Tailwind CSS, Pytest

---

### Task 1: Create failing unit tests for the clone logic

**Files:**
- Create: `app/Planning/tests/test_load_categories.py`

**Step 1: Write the failing test**

```python
import pytest
from django.urls import reverse
from app.Project.tests.factories import AccountFactory, ProjectFactory, CategoryFactory, SubCategoryFactory, GroupFactory, ProjectRole, Role

@pytest.mark.django_db
class TestLoadWBSCategories:
    def setup_method(self):
        self.project = ProjectFactory(name="Target Project")
        self.source_project = ProjectFactory(name="Source Project")
        self.user = AccountFactory()
        self.project.users.add(self.user)
        self.source_project.users.add(self.user)
        ProjectRole.objects.create(project=self.project, user=self.user, role=Role.ADMIN)
        
        # Create WBS structure on source project
        self.source_cat = CategoryFactory(project=self.source_project, name="Source L1")
        self.source_sub = SubCategoryFactory(category=self.source_cat, project=self.source_project, name="Source L2")
        self.source_grp = GroupFactory(sub_category=self.source_sub, project=self.source_project, name="Source L3")
        
        self.url = reverse("planning:load-categories", kwargs={"project_pk": self.project.pk})

    def test_load_categories_success(self, client):
        client.force_login(self.user)
        response = client.post(self.url, {"source_project": self.source_project.pk})
        
        assert response.status_code == 302
        assert self.project.categories.filter(name="Source L1").exists()
        
        target_cat = self.project.categories.get(name="Source L1")
        assert target_cat.subcategories.filter(name="Source L2").exists()
        
        target_sub = target_cat.subcategories.get(name="Source L2")
        assert target_sub.groups.filter(name="Source L3").exists()
```

**Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest app/Planning/tests/test_load_categories.py -v`
Expected: FAIL with `NoReverseMatch` (URL pattern not defined yet).

---

### Task 2: Implement URL Route and Backend View

**Files:**
- Modify: `app/Planning/urls.py`
- Modify: `app/Planning/views.py`

**Step 1: Implement the view in `app/Planning/views.py`**

```python
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from app.Project.projects.projects_models import Category, SubCategory, Group, Project

class LoadWBSCategoriesView(PlanningMixin, View):
    def post(self, request, *args, **kwargs):
        project = self.get_project()
        source_project_id = request.POST.get("source_project")
        if not source_project_id:
            messages.error(request, "Please select a project to load WBS levels from.")
            return redirect("planning:scope-planning", project_pk=project.pk)

        source_project = get_object_or_404(Project, pk=source_project_id)

        with transaction.atomic():
            # Delete existing empty WBS levels for the target project
            Category.objects.filter(project=project).delete()
            SubCategory.objects.filter(project=project).delete()
            Group.objects.filter(project=project).delete()

            # Clone WBS structure
            source_categories = Category.objects.filter(project=source_project, deleted=False).order_by("created_at")
            for sc in source_categories:
                tc = Category.objects.create(
                    project=project,
                    name=sc.name,
                    description=sc.description,
                    start_date=sc.start_date,
                    end_date=sc.end_date,
                    budget=sc.budget,
                    supply_only=sc.supply_only,
                    install_only=sc.install_only,
                    preliminaries=sc.preliminaries,
                )
                source_subcategories = SubCategory.objects.filter(category=sc, deleted=False).order_by("created_at")
                for ssc in source_subcategories:
                    tsc = SubCategory.objects.create(
                        project=project,
                        category=tc,
                        name=ssc.name,
                        description=ssc.description,
                        start_date=ssc.start_date,
                        end_date=ssc.end_date,
                        budget=ssc.budget,
                        supply_only=ssc.supply_only,
                        install_only=ssc.install_only,
                        preliminaries=ssc.preliminaries,
                    )
                    source_groups = Group.objects.filter(sub_category=ssc, deleted=False).order_by("created_at")
                    for sg in source_groups:
                        Group.objects.create(
                            project=project,
                            sub_category=tsc,
                            name=sg.name,
                            description=sg.description,
                            start_date=sg.start_date,
                            end_date=sg.end_date,
                            budget=sg.budget,
                            supply_only=sg.supply_only,
                            install_only=sg.install_only,
                            preliminaries=sg.preliminaries,
                        )

        messages.success(request, f"Successfully loaded WBS levels from '{source_project.name}'.")
        return redirect("planning:scope-planning", project_pk=project.pk)
```

**Step 2: Add view to `app/Planning/urls.py`**

```python
    path(
        "<int:project_pk>/scope-planning/load-categories/",
        LoadWBSCategoriesView.as_view(),
        name="load-categories",
    ),
```

**Step 3: Run pytest to verify passing**

Run: `.venv\Scripts\python.exe -m pytest app/Planning/tests/test_load_categories.py -v`
Expected: PASS.

---

### Task 3: Refactor the Frontend Scope Planning Page

**Files:**
- Modify: `app/Planning/templates/planning/scope_planning.html`
- Modify: `app/Planning/views.py` (add `other_projects` to context)

**Step 1: Update `ScopePlanningView.get_context_data` in `app/Planning/views.py`**

Add `other_projects` to context:
```python
        context["other_projects"] = Project.objects.filter(
            deleted=False,
            categories__deleted=False
        ).exclude(pk=project.pk).distinct().order_by("name")
```

**Step 2: Add Load Categories button and modal to `scope_planning.html`**

Next to the `Add WBS Level 1` button:
```html
                {% if other_projects %}
                <button type="button"
                        onclick="openLoadCategoriesModal()"
                        class="inline-flex items-center px-5 py-2.5 mr-3 text-sm font-semibold text-gray-700 bg-white rounded-lg border border-gray-300 shadow-md transition-all duration-200 hover:bg-gray-50 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    {% heroicon_outline "arrow-down-tray" size="18" class="mr-2 text-gray-500" %}
                    <span>Load Categories</span>
                </button>
                {% endif %}
```

Also add the modal markup:
```html
    <!-- Load Categories Modal -->
    <div id="loadCategoriesModal"
         class="hidden fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-50">
        <div class="flex items-center justify-center min-h-screen p-4">
            <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
                <div class="px-6 py-4 border-b border-gray-200">
                    <div class="flex items-center justify-between">
                        <h3 class="text-lg font-semibold text-gray-900">Load WBS Levels</h3>
                        <button type="button"
                                onclick="closeLoadCategoriesModal()"
                                class="text-gray-400 hover:text-gray-500">
                            {% heroicon_outline "x-mark" size="20" %}
                        </button>
                    </div>
                </div>
                <form method="post" action="{% url 'planning:load-categories' project.pk %}">
                    {% csrf_token %}
                    <div class="px-6 py-4 space-y-4">
                        <p class="text-sm text-gray-600">
                            Select a project to load WBS levels (Categories, SubCategories, and Groups) from. This will replace the current WBS levels on this project.
                        </p>
                        <div>
                            <label for="load_source_project" class="block text-sm font-medium text-gray-700">Source Project</label>
                            <select name="source_project" id="load_source_project" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                                <option value="">-- Choose a project --</option>
                                {% for p in other_projects %}
                                    <option value="{{ p.pk }}">{{ p.name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
                        <button type="button"
                                onclick="closeLoadCategoriesModal()"
                                class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                            Cancel
                        </button>
                        <button type="submit"
                                class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700">
                            Load
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
```

And JS handlers in `extra_js` block:
```javascript
        const loadCategoriesModal = document.getElementById("loadCategoriesModal");
        function openLoadCategoriesModal() {
            loadCategoriesModal.classList.remove('hidden');
        }
        function closeLoadCategoriesModal() {
            loadCategoriesModal.classList.add('hidden');
        }
```
