# Design: Design Development UI Refactor and Reusable Back Button

## Goal
The goal is to refactor the Design Development overview template (`design_development.html`) to be user-friendly, bug-free, and to make the project back button reusable across multiple overview pages.

---

## 1. Reusable Back Button

### Proposed Approach
Create a single global template partial at `app/templates/components/back_button.html` that can be included by any view template in the project.

#### Component Design
The component will accept:
- `url`: The target URL (e.g., `{% url 'project:project-management' project.pk %}`).
- `text`: The label text (e.g., `"Back to Project"` or `"Back to Project Management"`).
- `style`: Visual style variation.
  - `"white"` (default for dark/gradient headers): A semi-transparent white backdrop button with clean white text/icons.
  - `"gray"` (default for light headers): A gray border white-background button.

#### HTML Template (`app/templates/components/back_button.html`)
```html
{% load heroicons %}

{% if style == "white" %}
    <a href="{{ url }}"
       class="inline-flex items-center px-4 py-2 border border-white/20 text-sm font-semibold rounded-lg text-white bg-white/10 hover:bg-white/20 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-white/50 transition-all duration-200 shadow-md">
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

---

## 2. Design Development UI Refactoring

### A. Fix Hierarchy Nesting Bug
Currently, in `design_development.html`, the Level 3 (Groups) loop is placed outside the `id="subcategory-{{ subcategory.id }}"` wrapper. We will move the closing `</div>` of the wrapper to be *after* the groups loop ends, ensuring Level 3 is hidden/shown when Level 2 collapses/expands.

### B. Correct Empty State copy
Inside the subcategories loop `{% empty %}` block, the message currently says `"No categories found for this project"`. We will change it to `"No subcategories found for this category"`.

### C. Elevate Action Link Styling
We will refactor the action links in the header card (e.g., `+ L1 Category`, `+ L2 SubCategory`, etc.) from simple underlined links to clean, rounded button badges that look modern and feel interactive:
- **Tailwind styling**: `inline-flex items-center px-3 py-1.5 border border-white/20 rounded-lg text-xs font-semibold text-white bg-white/10 hover:bg-white/20 transition-all duration-200`

---

## 3. Scope of Impacted Templates
The following templates will be updated to use the new reusable back button:
1. `app/Planning/templates/planning/overview/design_development.html` (Uses `style="white"`)
2. `app/Planning/templates/planning/overview/tender_documentation.html` (Uses `style="gray"`)
3. `app/Planning/templates/planning/overview/tender_process.html` (Uses `style="gray"`)
4. `app/Planning/templates/planning/budget_forecast.html` (Uses `style="gray"`)
5. `app/Planning/templates/planning/scope_planning.html` (Uses `style="gray"`)
