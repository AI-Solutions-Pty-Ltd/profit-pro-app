# System Library Municipalities Register Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Create a register in the System Library to manage South African provinces and municipalities using the existing `Account.Municipality` model.

**Architecture:** We will reuse the existing `Municipality` model and its unique keys, defining a form, view logic, Excel import handlers, and list template inside the `Estimator` app, integrating it as a new navigation tab in the System Library.

**Tech Stack:** Django, Tailwind CSS, openpyxl (Excel parsing).

---

### Task 1: Add MunicipalityFactory to Account factories

**Files:**
- Modify: [factories.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/factories.py)

**Step 1: Write the failing test**
We will add a new test in `app/Account/tests/test_models.py` that imports and uses `MunicipalityFactory` to create a Municipality.

Modify: [test_models.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/test_models.py)
Add a test method to verify `MunicipalityFactory` creation:
```python
def test_municipality_factory(self):
    from app.Account.tests.factories import MunicipalityFactory
    municipality = MunicipalityFactory(province="Western Cape", municipality_name="George")
    assert municipality.id is not None
    assert municipality.province == "Western Cape"
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_models.py -k test_municipality_factory`
Expected: FAIL with `ImportError: cannot import name 'MunicipalityFactory'`

**Step 3: Write minimal implementation**
Modify: [factories.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Account/tests/factories.py)
Import `Municipality` and add `MunicipalityFactory`:
```python
from app.Account.models import Account, Suburb, Town, Municipality

class MunicipalityFactory(DjangoModelFactory):
    """Factory for Municipality model."""

    class Meta:
        model = Municipality
        django_get_or_create = ("province", "municipality_name", "code")

    province = Sequence(lambda n: f"Province {n}")
    municipality_name = Sequence(lambda n: f"Municipality {n}")
    code = Sequence(lambda n: f"MUN{n:03d}")
    district = Sequence(lambda n: f"District {n}")
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Account/tests/test_models.py -k test_municipality_factory`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Account/tests/factories.py app/Account/tests/test_models.py
git commit -m "test: add MunicipalityFactory and verify creation"
```

---

### Task 2: Define SystemMunicipalityForm in Estimator forms

**Files:**
- Modify: [forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Estimator/forms.py)

**Step 1: Write the failing test**
We will add a new test in `app/Estimator/tests/test_system_municipalities.py` (which we will create) to import and validate `SystemMunicipalityForm`.

Create: `app/Estimator/tests/test_system_municipalities.py`
```python
import pytest
from app.Estimator.forms import SystemMunicipalityForm

def test_system_municipality_form_validation():
    form_data = {
        "province": "Gauteng",
        "municipality_name": "City of Johannesburg",
        "code": "COJ",
        "district": "Johannesburg",
    }
    form = SystemMunicipalityForm(data=form_data)
    assert form.is_valid()
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Estimator/tests/test_system_municipalities.py -k test_system_municipality_form_validation`
Expected: FAIL with `ImportError: cannot import name 'SystemMunicipalityForm'`

**Step 3: Write minimal implementation**
Modify: [forms.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Estimator/forms.py)
Import `Municipality` and define `SystemMunicipalityForm`:
```python
from app.Account.models import Municipality

class SystemMunicipalityForm(forms.ModelForm):
    class Meta:
        model = Municipality
        fields = ["province", "municipality_name", "code", "district"]
        widgets = {
            "province": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Western Cape"}
            ),
            "municipality_name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. George Local Municipality",
                }
            ),
            "code": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. WC044"}
            ),
            "district": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Garden Route"}
            ),
        }
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Estimator/tests/test_system_municipalities.py -k test_system_municipality_form_validation`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Estimator/forms.py app/Estimator/tests/test_system_municipalities.py
git commit -m "feat: implement SystemMunicipalityForm and verify validation"
```

---

### Task 3: Create MunicipalityImporter in Estimator importers

**Files:**
- Modify: [importers.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Estimator/importers.py)

**Step 1: Write the failing test**
We will add a test in `app/Estimator/tests/test_system_municipalities.py` that runs the importer on a mock/actual Excel sheet and verifies that records are created/updated correctly.

Modify: `app/Estimator/tests/test_system_municipalities.py`
Add:
```python
import os
import openpyxl
from app.Account.models import Municipality
from app.Estimator.importers import MunicipalityImporter

def test_municipality_importer(tmp_path):
    # Create simple excel sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Municipalities"
    ws.append(["Province", "Municipality Name", "Code", "District"])
    ws.append(["Western Cape", "George Local Municipality", "WC044", "Garden Route"])
    
    file_path = os.path.join(tmp_path, "test_mun.xlsx")
    wb.save(file_path)

    importer = MunicipalityImporter(file_path)
    result = importer.run()

    assert result["created"] == 1
    assert result["skipped"] == 0
    
    # Verify DB record
    mun = Municipality.objects.get(code="WC044")
    assert mun.province == "Western Cape"
    assert mun.municipality_name == "George Local Municipality"
    assert mun.district == "Garden Route"
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Estimator/tests/test_system_municipalities.py -k test_municipality_importer`
Expected: FAIL with `ImportError: cannot import name 'MunicipalityImporter'`

**Step 3: Write minimal implementation**
Modify: [importers.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Estimator/importers.py)
Import `Municipality` and define `MunicipalityImporter`:
```python
from app.Account.models import Municipality

class MunicipalityImporter:
    """Import Municipalities from Excel.

    Expected columns: Province | Municipality Name | Code | District
    """

    SHEET_KEYWORDS = [
        "municipality",
        "municipalities",
        "province",
        "provinces",
    ]

    def __init__(self, path, project=None, company=None):
        self.path = path
        self.project = project
        self.company = company

    def run(self):
        wb = openpyxl.load_workbook(self.path, data_only=True)
        ws = _find_sheet(wb, self.SHEET_KEYWORDS)
        created = updated = skipped = 0
        
        # Find header row
        header_row_idx = _find_header_row(ws, ["province", "municipality", "code"])
        
        for row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
            if not row or not any(row):
                continue
            province = _safe_str(row[0]) if len(row) > 0 else ""
            municipality_name = _safe_str(row[1]) if len(row) > 1 else ""
            code = _safe_str(row[2]) if len(row) > 2 else ""
            district = _safe_str(row[3]) if len(row) > 3 else ""
            
            if not province or not municipality_name or not code:
                skipped += 1
                continue

            obj, is_new = Municipality.objects.update_or_create(
                province=province,
                municipality_name=municipality_name,
                code=code,
                defaults={"district": district},
            )
            if is_new:
                created += 1
            else:
                updated += 1
        return {"created": created, "updated": updated, "skipped": skipped}
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Estimator/tests/test_system_municipalities.py -k test_municipality_importer`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Estimator/importers.py app/Estimator/tests/test_system_municipalities.py
git commit -m "feat: implement MunicipalityImporter for Excel parsing"
```

---

### Task 4: Define Views in Estimator views

**Files:**
- Modify: [views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Estimator/views.py)

**Step 1: Write the failing test**
We will add views test methods in `app/Estimator/tests/test_system_municipalities.py` checking URL resolution, rendering, POSTing new municipality (as staff), and verifying list updates.

Modify: `app/Estimator/tests/test_system_municipalities.py`
Add:
```python
from django.urls import reverse
from app.Account.tests.factories import SuperuserFactory, UserFactory, MunicipalityFactory

@pytest.mark.django_db
def test_system_municipalities_views(client):
    url = reverse("estimator:sys_municipalities")
    
    # Guest/Regular user redirected or denied
    user = UserFactory()
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403 or response.status_code == 302

    # Staff user allowed
    admin = SuperuserFactory()
    client.force_login(admin)
    response = client.get(url)
    assert response.status_code == 200

    # Add a municipality
    post_data = {
        "province": "Western Cape",
        "municipality_name": "George Local Municipality",
        "code": "WC044",
        "district": "Garden Route",
    }
    response = client.post(url, data=post_data)
    assert response.status_code == 302 # Redirect on success
    assert Municipality.objects.filter(code="WC044").exists()
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Estimator/tests/test_system_municipalities.py -k test_system_municipalities_views`
Expected: FAIL with `NoReverseMatch: 'sys_municipalities' is not a registered namespace` (or similar url error)

**Step 3: Write minimal implementation**
Modify: [views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Estimator/views.py)
We need to import `Municipality` from `app.Account.models`, `SystemMunicipalityForm` from `.forms`, and `MunicipalityImporter` from `.importers`.
Let's add the views:
```python
from app.Account.models import Municipality
from .forms import SystemMunicipalityForm
from .importers import MunicipalityImporter

# ── System Municipalities ─────────────────────────────────────────────


class SystemMunicipalityListView(SystemLibraryMixin, ListView):
    model = Municipality
    template_name = "estimator/system/municipality_list.html"
    context_object_name = "municipalities"
    paginate_by = 50

    def get_queryset(self):
        qs = Municipality.objects.all()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(province__icontains=q)
                | Q(municipality_name__icontains=q)
                | Q(code__icontains=q)
                | Q(district__icontains=q)
            )
        province = self.request.GET.get("province", "").strip()
        if province:
            qs = qs.filter(province=province)
        return qs.order_by("province", "municipality_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = context.get("form", SystemMunicipalityForm())
        context["provinces"] = (
            Municipality.objects.exclude(province="")
            .values_list("province", flat=True)
            .distinct()
            .order_by("province")
        )
        context["f_q"] = self.request.GET.get("q", "")
        context["f_province"] = self.request.GET.get("province", "")
        context["query_params"] = _pagination_query_params(self.request)
        return context

    def post(self, request, *args, **kwargs):
        if _handle_clear_action(
            request, Municipality.objects.all(), label="municipalities"
        ):
            return redirect(reverse("estimator:sys_municipalities"))
        if _handle_bulk_action(request, Municipality.objects.all()):
            return redirect(reverse("estimator:sys_municipalities"))
        form = SystemMunicipalityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Municipality added successfully.")
            return redirect(reverse("estimator:sys_municipalities"))
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


class SystemMunicipalityUploadView(SystemLibraryMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upload_title"] = "Upload Municipalities"
        context["upload_description"] = (
            "Upload South African provinces and municipalities from an Excel template."
        )
        context["parent_template"] = "estimator/system/base_system.html"
        context["download_url_name"] = "estimator:sys_download_municipality_template"
        return context

    def form_valid(self, form):
        return _handle_upload(
            self.request, MunicipalityImporter, "estimator:sys_municipalities", "Municipalities"
        )


class DownloadSystemMunicipalityTemplateView(SystemLibraryMixin, View):
    def get(self, request):
        return _generate_template(
            ["Province", "Municipality Name", "Code", "District"],
            "system_municipalities_template.xlsx",
        )
```

**Step 4: Run test to verify it passes**
(Wait, we need to register the urls first, so let's continue to Task 5 to make this test pass.)

---

### Task 5: Register URLs in Estimator urls

**Files:**
- Modify: [urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Estimator/urls.py)

**Step 1: Write the failing test**
(The test `test_system_municipalities_views` in Task 4 serves as the failing test.)

**Step 2: Run test to verify it fails**
Expected: FAIL with `NoReverseMatch`

**Step 3: Write minimal implementation**
Modify: [urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Estimator/urls.py)
Add the paths:
```python
    path(
        "system/municipalities/",
        views.SystemMunicipalityListView.as_view(),
        name="sys_municipalities",
    ),
    path(
        "system/municipalities/upload/",
        views.SystemMunicipalityUploadView.as_view(),
        name="sys_municipality_upload",
    ),
    path(
        "system/municipalities/template/",
        views.DownloadSystemMunicipalityTemplateView.as_view(),
        name="sys_download_municipality_template",
    ),
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Estimator/tests/test_system_municipalities.py`
Expected: PASS (except template rendering since the file does not exist yet)

**Step 5: Commit**
```bash
git add app/Estimator/views.py app/Estimator/urls.py
git commit -m "feat: add urls and views for system municipalities"
```

---

### Task 6: Create Template and Add Navigation Tab

**Files:**
- Create: `app/Estimator/templates/estimator/system/municipality_list.html`
- Modify: [base_system.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Estimator/templates/estimator/system/base_system.html)

**Step 1: Write the failing test**
Let's add a test checking template existence and tab rendering:
Modify: `app/Estimator/tests/test_system_municipalities.py`
Add:
```python
@pytest.mark.django_db
def test_tab_in_base_system(client):
    admin = SuperuserFactory()
    client.force_login(admin)
    url = reverse("estimator:sys_trade_codes")
    response = client.get(url)
    assert response.status_code == 200
    assert b"sys_municipalities" in response.content
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Estimator/tests/test_system_municipalities.py -k test_tab_in_base_system`
Expected: FAIL with `AssertionError: assert b"sys_municipalities" in ...`

**Step 3: Write minimal implementation**
1. Modify: [base_system.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Estimator/templates/estimator/system/base_system.html)
Add tab after "Item Library":
```html
                        <a href="{% url 'estimator:sys_municipalities' %}"
                           class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm {% if url_name == 'sys_municipalities' or url_name == 'sys_municipality_upload' %}border-indigo-500 text-indigo-600{% else %}border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300{% endif %}">
                            {% heroicon_outline "map" class="inline-block mr-1 w-4 h-4" %}
                            Municipalities
                        </a>
```

2. Create: `app/Estimator/templates/estimator/system/municipality_list.html`
```html
{% extends "estimator/system/base_system.html" %}
{% block title %}Municipalities - System Library{% endblock %}
{% block sub_content %}
    <div class="sm:flex sm:items-center sm:justify-between mb-6">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">Municipalities</h1>
            <p class="mt-1 text-sm text-gray-500">Standard South African provinces and municipalities list.</p>
        </div>
        <div class="mt-4 sm:mt-0 flex gap-2">
            <a href="{% url 'estimator:sys_municipality_upload' %}"
               class="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500">
                {% heroicon_outline "arrow-up-tray" class="w-4 h-4 mr-1.5 -ml-0.5" %}
                Upload
            </a>
            <a href="{% url 'estimator:sys_download_municipality_template' %}"
               class="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50">
                {% heroicon_outline "arrow-down-tray" class="w-4 h-4 mr-1.5 -ml-0.5" %}
                Template
            </a>
            <button type="button"
                    onclick="document.getElementById('municipality-form').classList.toggle('hidden')"
                    class="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500">
                {% heroicon_outline "plus" class="w-5 h-5 mr-1.5 -ml-0.5" %}
                Add Municipality
            </button>
            {% include "estimator/_clear_all_modal.html" with clear_sheet_label="Municipalities" %}
        </div>
    </div>

    <!-- Add Municipality Form -->
    <div id="municipality-form" class="{% if not form.errors %}hidden{% endif %} mb-6">
        <div class="overflow-hidden bg-white shadow-sm rounded-lg">
            <div class="px-4 py-5 sm:p-6">
                <h3 class="text-base font-semibold text-gray-900 mb-4">New Municipality</h3>
                <form method="post">
                    {% csrf_token %}
                    {% if form.errors %}
                        <div class="rounded-md bg-red-50 p-4 mb-4">
                            <div class="text-sm text-red-700">
                                {% for field, errors in form.errors.items %}
                                    {% for error in errors %}<p>{{ field }}: {{ error }}</p>{% endfor %}
                                {% endfor %}
                            </div>
                        </div>
                    {% endif %}
                    <div class="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-4">
                        <div>
                            <label for="id_province" class="block text-sm font-medium text-gray-700">Province</label>
                            <div class="mt-1">{{ form.province }}</div>
                        </div>
                        <div>
                            <label for="id_municipality_name" class="block text-sm font-medium text-gray-700">Municipality Name</label>
                            <div class="mt-1">{{ form.municipality_name }}</div>
                        </div>
                        <div>
                            <label for="id_code" class="block text-sm font-medium text-gray-700">Code</label>
                            <div class="mt-1">{{ form.code }}</div>
                        </div>
                        <div>
                            <label for="id_district" class="block text-sm font-medium text-gray-700">District</label>
                            <div class="mt-1">{{ form.district }}</div>
                        </div>
                    </div>
                    <div class="mt-4 flex justify-end gap-x-3">
                        <button type="button"
                                onclick="document.getElementById('municipality-form').classList.add('hidden')"
                                class="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50">
                            Cancel
                        </button>
                        <button type="submit"
                                class="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500">
                            Save Municipality
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Search & Filters -->
    <div class="bg-white shadow-sm rounded-lg p-4 mb-4">
        <form method="get" id="filter-form" class="flex flex-wrap items-end gap-3">
            <div class="flex-1 min-w-[220px]">
                <label class="block text-[10px] font-semibold uppercase tracking-wider text-gray-500 mb-1">Search</label>
                <input type="text"
                       id="cost-search"
                       name="q"
                       value="{{ f_q }}"
                       placeholder="Province, name, code, district…"
                       autocomplete="off"
                       class="block w-full rounded-md border-0 py-1.5 px-2 text-xs text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-indigo-600 bg-white">
            </div>
            <div class="min-w-[150px]">
                <label class="block text-[10px] font-semibold uppercase tracking-wider text-gray-500 mb-1">Province</label>
                <select name="province"
                        onchange="this.form.submit()"
                        class="block w-full rounded-md border-0 py-1.5 pl-2 pr-8 text-xs text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-indigo-600 bg-white">
                    <option value="">All Provinces</option>
                    {% for p in provinces %}
                        <option value="{{ p }}" {% if f_province == p %}selected{% endif %}>{{ p }}</option>
                    {% endfor %}
                </select>
            </div>
            {% if f_q or f_province %}
                <a href="{% url 'estimator:sys_municipalities' %}"
                   class="inline-flex items-center rounded-md bg-gray-100 px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200 ring-1 ring-inset ring-gray-300">
                    {% heroicon_outline "x-mark" class="w-3.5 h-3.5 mr-1" %}
                    Clear
                </a>
            {% endif %}
        </form>
    </div>

    <!-- Table -->
    <form method="post" id="bulk-form">
        {% csrf_token %}
        {% include "estimator/_bulk_toolbar.html" %}
        <div class="overflow-hidden bg-white shadow-sm rounded-lg">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="w-8 py-3.5 pl-4 pr-2 sm:pl-6">
                                <input type="checkbox"
                                       id="select-all"
                                       class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600">
                            </th>
                            <th scope="col" class="px-3 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                                Province
                            </th>
                            <th scope="col" class="px-3 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                                Municipality Name
                            </th>
                            <th scope="col" class="px-3 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                                Code
                            </th>
                            <th scope="col" class="px-3 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                                District
                            </th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 bg-white">
                        {% for mun in municipalities %}
                            <tr class="bulk-row hover:bg-gray-50"
                                data-search="{{ mun.province|lower }} {{ mun.municipality_name|lower }} {{ mun.code|lower }} {{ mun.district|lower }}">
                                <td class="py-3 pl-4 pr-2 sm:pl-6">
                                    <input type="checkbox"
                                           name="ids"
                                           value="{{ mun.id }}"
                                           class="row-check h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600">
                                </td>
                                <td class="whitespace-nowrap px-3 py-3 text-sm text-gray-900">{{ mun.province }}</td>
                                <td class="whitespace-nowrap px-3 py-3 text-sm text-gray-900 font-medium">{{ mun.municipality_name }}</td>
                                <td class="whitespace-nowrap px-3 py-3 text-sm text-gray-500">
                                    <span class="inline-flex items-center rounded-md bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-700/10">
                                        {{ mun.code }}
                                    </span>
                                </td>
                                <td class="whitespace-nowrap px-3 py-3 text-sm text-gray-500">{{ mun.district|default:"-" }}</td>
                            </tr>
                        {% empty %}
                            <tr>
                                <td colspan="5" class="px-6 py-12 text-center text-sm text-gray-500">No municipalities found.</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </form>
    {% include "estimator/_bulk_script.html" %}
    {% include "estimator/_pagination.html" %}
{% endblock %}
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Estimator/tests/test_system_municipalities.py`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Estimator/templates/estimator/system/base_system.html app/Estimator/templates/estimator/system/municipality_list.html
git commit -m "feat: implement template and tab for system municipalities"
```
