# Design Development UI Refactor and Reusable Back Button Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Refactor the Design Development UI for better usability/bug-free collapse-expand behavior and create a reusable back button template component used across all planning and overview pages.

**Architecture:** A global reusable Django template partial `components/back_button.html` will be created to support custom styles (white backdrop/gray border) and URLs. The `design_development.html` template will be updated to resolve its subcategory HTML nesting/empty state copy bugs and style its actions row with Tailwind CSS.

**Tech Stack:** Django, Python, HTML/Tailwind CSS, Heroicons.

---

### Task 1: Create Reusable Back Button Component

**Files:**
- Create: [back_button.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/templates/components/back_button.html)

**Step 1: Write implementation**
Create the file with the following contents:
```html
{% load heroicons %}

{% if style == "white" %}
    <a href="{{ url }}"
       class="inline-flex items-center px-4 py-2 border border-white/20 text-sm font-semibold rounded-lg text-white bg-white/10 hover:bg-white/20 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-white/50 transition-all duration-200 shadow-lg">
        {% heroicon_outline "arrow-left" size="18" class="mr-2 text-white/95" %}
        <span>{{ text|default:"Back" }}</span>
    </a>
{% else %}
    <a href="{{ url }}"
       class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-semibold rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-200">
        {% heroicon_outline "arrow-left" size="18" class="mr-2 text-gray-500" %}
        <span>{{ text|default:"Back" }}</span>
    </a>
{% endif %}
```

**Step 2: Commit**
```bash
git add app/templates/components/back_button.html
git commit -m "feat: add reusable back button component"
```

---

### Task 2: Refactor Design Development UI and Integrate Back Button

**Files:**
- Modify: [design_development.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/overview/design_development.html)

**Step 1: Refactor UI, nest subcategories/groups properly, fix empty message, and add button styling**
- Replace the raw back link in the header card with:
  ```html
  {% include "components/back_button.html" with url=view.get_project_management_url text="Back to Project" style="white" %}
  ```
  *(Note: check if view has `get_project_management_url` or use `{% url 'project:project-management' project.pk %}`)*
- In the action links row in the header, change:
  ```html
  <a href="{% url 'planning:design-category-create' project.pk %}"
     class="text-sm text-indigo-200 hover:text-white underline transition-colors">+ L1 Category</a>
  ```
  and other sibling links, to use styled Tailwind button badges:
  ```html
  <a href="{% url 'planning:design-category-create' project.pk %}"
     class="inline-flex items-center px-3 py-1.5 border border-white/20 rounded-lg text-xs font-semibold text-white bg-white/10 hover:bg-white/20 transition-all duration-200 shadow-sm">+ L1 Category</a>
  ```
- Move the early closing `</div>` tag for the subcategory wrapper:
  Find:
  ```html
  297:                             </div>
  298:                             <!-- Added closing div tag here -->
  299:                             <!-- Groups within subcategory -->
  ```
  *(Remove `</div>` on line 297, as well as the comment, and close it after the groups loop ends at line 429)*
- Correct the empty message inside the subcategories loop `{% empty %}` block:
  Change:
  ```html
  <p class="text-center text-gray-500 py-8">No categories found for this project</p>
  ```
  To:
  ```html
  <p class="text-center text-gray-500 py-8">No subcategories found for this category</p>
  ```

**Step 2: Verify tests run cleanly**
Run: `.venv\Scripts\python.exe -m pytest app/Planning/tests/ -v`

**Step 3: Commit**
```bash
git add app/Planning/templates/planning/overview/design_development.html
git commit -m "feat: refactor design_development.html UI and integrate back_button"
```

---

### Task 3: Integrate Back Button in Overview Templates

**Files:**
- Modify: [tender_documentation.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/overview/tender_documentation.html)
- Modify: [tender_process.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/overview/tender_process.html)

**Step 1: Replace raw back buttons**
Include the reusable back button component with `style="gray"` and target URL:
```html
{% include "components/back_button.html" with url=view.get_project_management_url text="Back" style="gray" %}
```

**Step 2: Commit**
```bash
git add app/Planning/templates/planning/overview/tender_documentation.html app/Planning/templates/planning/overview/tender_process.html
git commit -m "feat: integrate reusable back button in tender documentation and process overviews"
```

---

### Task 4: Integrate Back Button in Main Planning Templates

**Files:**
- Modify: [budget_forecast.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/budget_forecast.html)
- Modify: [scope_planning.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Planning/templates/planning/scope_planning.html)

**Step 1: Replace back buttons in footer**
Include the reusable back button component in the footer of both pages:
```html
{% include "components/back_button.html" with url=view.get_project_management_url text="Back to Project Management" style="gray" %}
```

**Step 2: Run all tests to verify completeness**
Run: `.venv\Scripts\python.exe -m pytest`

**Step 3: Commit**
```bash
git add app/Planning/templates/planning/budget_forecast.html app/Planning/templates/planning/scope_planning.html
git commit -m "feat: integrate reusable back button in budget_forecast and scope_planning templates"
```
