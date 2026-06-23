# Construction Milestones Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Create a feature to setup construction milestones under the project Work Breakdown Structures panel and import 20 standard construction milestones.

**Architecture:** Use the existing `Milestone` model and extend `Milestone` views to support a redirect parameter `next` so setup forms return back to the setup dashboard. Add setup routes and templates for listing and importing standard milestones.

**Tech Stack:** Python 3.11, Django, Tailwind CSS, Heroicons.

---

### Task 1: Update Existing Milestone Views for Redirect support

**Files:**
- Modify: `app/Project/milestone_schedules/milestone_views.py`
- Test: `app/Project/tests/test_milestones.py`

**Step 1: Write the failing test**

We will write tests in a new file `app/Project/tests/test_milestones.py` to verify that `next` parameter redirects are respected by Milestone Create, Update, and Delete views.

```python
import pytest
from django.urls import reverse
from app.Project.tests.factories import ProjectFactory, MilestoneFactory, AccountFactory
from app.Project.models import Role

@pytest.mark.django_db
class TestMilestoneRedirects:
    def test_create_respects_next_param(self, client):
        project = ProjectFactory()
        user = AccountFactory()
        project.users.add(user)
        # Grant permission
        project.project_roles.create(user=user, role=Role.ADMIN)
        client.force_login(user)

        url = reverse("project:milestone-create", kwargs={"project_pk": project.pk})
        next_url = "/some/redirect/url/"
        response = client.post(
            f"{url}?next={next_url}",
            {
                "name": "New Test Milestone",
                "planned_date": "2026-06-30",
                "sequence": 0,
            }
        )
        assert response.status_code == 302
        assert response.url == next_url
```

**Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_milestones.py -v`
Expected: FAIL (file does not exist or test fails because `next` parameter is not respected)

**Step 3: Write minimal implementation**

Modify `get_success_url` and `get_context_data` in `MilestoneCreateView`, `MilestoneUpdateView`, and `MilestoneDeleteView` in `app/Project/milestone_schedules/milestone_views.py`.

```python
    def get_success_url(self) -> str:
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url:
            return next_url
        return reverse(
            "project:time-forecast", kwargs={"project_pk": self.get_project().pk}
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        context.update(
            {
                "project": self.get_project(),
                "back_url": next_url or reverse("project:time-forecast", kwargs={"project_pk": self.get_project().pk}),
            }
        )
        return context
```

**Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_milestones.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/Project/milestone_schedules/milestone_views.py app/Project/tests/test_milestones.py
git commit -m "feat: add next query parameter redirect to Milestone Create, Update, Delete views"
```

---

### Task 2: Add Milestone Setup and Bulk Load Views and Routing

**Files:**
- Modify: `app/Project/milestone_schedules/milestone_urls.py`
- Modify: `app/Project/milestone_schedules/milestone_views.py`
- Test: `app/Project/tests/test_milestones.py`

**Step 1: Write the failing test**

Add tests to `app/Project/tests/test_milestones.py` for setup list and bulk load default milestones views.

```python
@pytest.mark.django_db
class TestMilestoneSetup:
    def test_setup_list_view(self, client):
        project = ProjectFactory()
        user = AccountFactory()
        project.users.add(user)
        project.project_roles.create(user=user, role=Role.ADMIN)
        client.force_login(user)

        url = reverse("project:project-milestone-setup", kwargs={"project_pk": project.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_load_default_milestones(self, client):
        project = ProjectFactory(start_date="2026-06-01")
        user = AccountFactory()
        project.users.add(user)
        project.project_roles.create(user=user, role=Role.ADMIN)
        client.force_login(user)

        url = reverse("project:project-milestone-load-defaults", kwargs={"project_pk": project.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert project.milestones.count() == 20
        assert project.milestones.filter(name="Earthworks").exists()
```

**Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_milestones.py -v`
Expected: FAIL (views or URL patterns don't exist)

**Step 3: Write minimal implementation**

1. Add urls to `app/Project/milestone_schedules/milestone_urls.py`:
```python
    path(
        "<int:project_pk>/setup/",
        milestone_views.MilestoneSetupView.as_view(),
        name="project-milestone-setup",
    ),
    path(
        "<int:project_pk>/setup/load-defaults/",
        milestone_views.MilestoneLoadDefaultsView.as_view(),
        name="project-milestone-load-defaults",
    ),
```

2. Add classes to `app/Project/milestone_schedules/milestone_views.py`:
```python
from django.views.generic import ListView
from django.views import View
from django.utils import timezone

class MilestoneSetupView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, ListView):
    """View to list and manage project milestones in Setup."""

    model = Milestone
    template_name = "project/milestones/milestone_manage.html"
    context_object_name = "milestones"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title=f"Setup: {project.name}",
                url=reverse("project:project-setup", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(title="Milestones", url=None),
        ]

    def get_queryset(self):
        """Return milestones sorted by sequence/date."""
        return Milestone.objects.filter(project=self.get_project()).order_by("sequence", "planned_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class MilestoneLoadDefaultsView(UserHasProjectRoleGenericMixin, View):
    """Post view to bulk load default construction milestones."""

    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        default_names = [
            "Earthworks", "Foundations", "Surface Beds", "External Envelope",
            "Internal divisions", "Doors and Windows", "Roof Construction", "Ceilings",
            "Floor Finishes", "Wall Finishes", "Ceiling Finishes", "Plastering",
            "Plumbing 1st Fix", "Plumbing 2nd Fix", "Electrical - 1st Fix",
            "Electrical - 2nd Fix", "Electrical - 3rd Fix", "Painting - Under Coat",
            "Painting - 1st Coat", "Painting - 2st Coat"
        ]

        existing_names = set(
            Milestone.objects.filter(project=project, deleted=False).values_list("name", flat=True)
        )
        planned_date = project.start_date or timezone.now().date()

        max_seq = Milestone.objects.filter(project=project, deleted=False).aggregate(
            max_seq=models.Max("sequence")
        )["max_seq"]
        current_seq = (max_seq + 1) if max_seq is not None else 0

        created_count = 0
        for name in default_names:
            if name not in existing_names:
                Milestone.objects.create(
                    project=project,
                    name=name,
                    planned_date=planned_date,
                    sequence=current_seq,
                )
                current_seq += 1
                created_count += 1

        if created_count > 0:
            messages.success(request, f"Loaded {created_count} default construction milestones successfully.")
        else:
            messages.info(request, "All default milestones are already loaded.")

        return redirect(reverse("project:project-milestone-setup", kwargs={"project_pk": project.pk}))
```

**Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_milestones.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/Project/milestone_schedules/milestone_views.py app/Project/milestone_schedules/milestone_urls.py
git commit -m "feat: add MilestoneSetupView and MilestoneLoadDefaultsView"
```

---

### Task 3: Create Milestone Setup Template

**Files:**
- Create: `app/Project/templates/project/milestones/milestone_manage.html`

**Step 1: Write minimal HTML template**

We will create `app/Project/templates/project/milestones/milestone_manage.html` using a premium and dynamic style matching `drawing_type_manage.html`.

```html
{% extends "base_full.html" %}
{% load heroicons %}
{% block content %}
    <div class="bg-white shadow-sm rounded-lg mb-6">
        <div class="px-6 py-4">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-2xl font-bold text-gray-900">Project Milestones</h1>
                    <p class="text-sm text-gray-600 mt-1">Configure and sequence construction milestones for {{ project.name }}</p>
                </div>
                <div class="flex items-center gap-3">
                    <form method="post" action="{% url 'project:project-milestone-load-defaults' project.pk %}">
                        {% csrf_token %}
                        <button type="submit"
                                class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
                            {% heroicon_outline "arrow-down-tray" size="16" %}
                            <span class="ml-2">Load Default Milestones</span>
                        </button>
                    </form>
                    <a href="{% url 'project:milestone-create' project.pk %}?next={% url 'project:project-milestone-setup' project.pk %}"
                       class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
                        {% heroicon_outline "plus" size="16" %}
                        <span class="ml-2">Add Milestone</span>
                    </a>
                    <a href="{% url 'project:project-setup' project.pk %}"
                       class="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
                        {% heroicon_outline "arrow-left" size="16" %}
                        <span class="ml-1">Back to Setup</span>
                    </a>
                </div>
            </div>
        </div>
    </div>

    <!-- Milestones List -->
    <div class="bg-white shadow-sm rounded-lg">
        <div class="px-6 py-4 border-b border-gray-200">
            <h2 class="text-lg font-semibold text-gray-900">Configured Milestones</h2>
            <p class="text-sm text-gray-500 mt-1">{{ milestones.count }} milestone{{ milestones.count|pluralize }} setup</p>
        </div>
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Seq</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Planned Date</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Forecast Date</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    {% for milestone in milestones %}
                        <tr class="hover:bg-gray-50 transition-colors">
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ milestone.sequence }}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ milestone.name }}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ milestone.planned_date|date:"d M Y" }}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {{ milestone.forecast_date|date:"d M Y"|default:"—" }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {{ milestone.status }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <div class="flex items-center justify-end gap-2">
                                    <a href="{% url 'project:milestone-update' project.pk milestone.pk %}?next={% url 'project:project-milestone-setup' project.pk %}"
                                       class="text-indigo-600 hover:text-indigo-900 transition-colors"
                                       title="Edit milestone">
                                        {% heroicon_outline "pencil" size="18" %}
                                    </a>
                                    <a href="{% url 'project:milestone-delete' project.pk milestone.pk %}?next={% url 'project:project-milestone-setup' project.pk %}"
                                       class="text-red-600 hover:text-red-900 transition-colors"
                                       title="Delete milestone">
                                        {% heroicon_outline "trash" size="18" %}
                                    </a>
                                </div>
                            </td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="6" class="px-6 py-12 text-center">
                                <div class="flex flex-col items-center">
                                    {% heroicon_outline "clock" size="48" class="text-gray-300 mb-4" %}
                                    <p class="text-sm text-gray-500 font-medium">No milestones configured yet</p>
                                    <p class="text-xs text-gray-400 mt-1">Click "Load Default Milestones" to pre-populate with standard construction milestones or "Add Milestone" to create custom ones.</p>
                                </div>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock content %}
```

**Step 2: Commit**

```bash
git add app/Project/templates/project/milestones/milestone_manage.html
git commit -m "feat: create milestone setup list template"
```

---

### Task 4: Update Existing Milestone Form Templates for Back Link

**Files:**
- Modify: `app/Project/templates/forecasts/milestone_form.html`
- Modify: `app/Project/templates/forecasts/milestone_confirm_delete.html`

**Step 1: Write modifications**

Replace the hardcoded `project:time-forecast` link back URLs with `back_url` context variable.

**Step 2: Commit**

```bash
git add app/Project/templates/forecasts/milestone_form.html app/Project/templates/forecasts/milestone_confirm_delete.html
git commit -m "feat: make milestone form and delete confirm templates respect back_url context"
```

---

### Task 5: Add Setup Card in Project Setup Dashboard

**Files:**
- Modify: `app/Project/templates/project/project_setup.html`

**Step 1: Write modifications**

Add the "Setup Construction Milestones" card.

```html
                    <div class="p-4 rounded-lg border border-gray-200 transition-all duration-200 hover:border-indigo-300 hover:shadow-md">
                        <h3 class="mb-1 text-sm font-semibold text-gray-900">Setup Construction Milestones</h3>
                        <p class="mb-3 text-xs text-gray-600">Create, sequence, and manage milestones, or load the standard construction milestones checklist</p>
                        <a href="{% url 'project:project-milestone-setup' project.pk %}"
                           class="inline-flex items-center px-3 py-2 text-sm font-medium text-indigo-600 bg-white rounded-md border border-indigo-600 shadow-sm transition-colors hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            {% heroicon_outline "clock" size="16" %}
                            <span class="ml-2">Setup Milestones</span>
                        </a>
                    </div>
```

**Step 2: Commit**

```bash
git add app/Project/templates/project/project_setup.html
git commit -m "feat: add Setup Construction Milestones card to Project Setup page"
```
