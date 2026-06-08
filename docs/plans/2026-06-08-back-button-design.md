# Design: Refactor Back Button to Business Management Center

## Goal
The goal is to refactor the back button in `app/SiteManagement/templates/site_management/_back_button.html` so that, instead of performing a simple history navigation (`window.history.back()`), it redirects the user directly to the Business Management Center page: `/project/company/<project_pk>/management/`.

## Approaches Considered

### Approach 1: Convert the `<button>` element to an `<a>` element (Recommended)
We replace the `<button>` element with an HTML anchor (`<a>`) and style it exactly like the original button to maintain layout consistency.
```html
<div class="mb-4">
    <a href="{% url 'project:company-management' project.pk %}"
       class="inline-flex items-center text-sm font-semibold text-gray-500 transition-all hover:text-indigo-600 group">
        <div class="p-1.5 mr-2.5 bg-gray-100 rounded-lg transition-colors group-hover:bg-indigo-50">
            {% heroicon_outline "arrow-left" size="16" %}
        </div>
        Back
    </a>
</div>
```
- **Pros:** Semantic HTML, standard navigation behavior, styling remains identical.
- **Cons:** None.

### Approach 2: Use JavaScript redirection in the `<button>` click handler
Keep the `<button>` element but modify `onclick`:
```html
<button onclick="window.location.href='{% url 'project:company-management' project.pk %}'" ...>
```
- **Pros:** Maintains the `<button>` tag.
- **Cons:** Non-semantic for standard navigation; relies on JavaScript.

## Recommendation
We proceed with **Approach 1** since it uses semantic HTML and standard template rendering. All views using templates that include `_back_button.html` inject `project` into the context, so `project.pk` will correctly resolve to the project's primary key.
