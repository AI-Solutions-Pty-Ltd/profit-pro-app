# Searchable Select Widget Documentation

The `SearchableSelectWidget` is a premium, custom-styled UI component designed to replace the standard Django `<select>` element. It provides a modern, interactive experience with built-in search capabilities and seamless integration with a "Quick Create" modal system.

---

## 🚀 Key Features

-   **🔍 Real-time Search**: Instant filtering of hundreds of options via a clean, glassmorphic search bar.
-   **✨ Premium UI/UX**: Built with Tailwind CSS and Heroicons, it features smooth slide-up animations, hovering effects, and responsive feedback.
-   **⚡ Dynamic Quick Create**: Integrated "Create New" button that opens an AJAX-driven modal for on-the-fly resource addition without leaving the current form.
-   **🔄 Automatic State Management**: Syncs user selection with a hidden native `<select>` element, ensuring total compatibility with standard Django form submission and validation.
-   **📦 Formset Compatibility**: Designed with relative DOM traversal, making it fully functional within dynamic Django Formsets and Inline Forms.
-   **♿ Progressive Enhancement**: Degrades gracefully to a standard select if JavaScript is disabled.

---

## 🛠️ Usage Guide

### 1. Import the Widget
First, import the widget in your Django forms file.

```python
from app.core.Utilities.widgets import SearchableSelectWidget
```

### 2. Apply to a Form Field
Assign the widget to a `ChoiceField` or `ModelChoiceField`.

```python
class LabourEntityForm(forms.ModelForm):
    class Meta:
        model = LabourEntity
        fields = ["skill_type", ...]
        widgets = {
            "skill_type": SearchableSelectWidget(
                attrs={"id": "skill_type_select"}, # Optional: unique ID
                create_url=True,                  # Enables the "Create New" button
                resource_type="skill_type"       # Slug used for the Quick Create registry
            ),
        }
```

### 3. Ensure Assets are Loaded
The widget includes its own logic via the `Media` class. Ensure your template renders `{{ form.media }}` or that `static/js/searchable_select.js` is included in your base layout.

### 4. Enable Quick Create (Optional)
To use the "Quick Create" feature, follow these sub-steps:

#### A. Inclusion
Ensure the `dynamic-quick-create-modal` partial is included in your page (usually in `layout.html` or the specific dashboard).

```html
{% include "modals/dynamic_quick_create_modal.html" %}
```

#### B. Registration
Register your model and form with the central `QuickCreateRegistry` in a file named `quick_create.py` within your app.

```python
# app/YourApp/quick_create.py
from app.core.dynamic_quick_create import registry
from .models import YourModel
from .forms import YourModelForm

registry.register(
    resource_type="your_resource_slug", # Must match resource_type in widget
    model=YourModel,
    form_class=YourModelForm,
    title="Create New Resource",
    needs_project=False # Set to True if the model requires a project FK
)
```

---

## 🎨 Advanced Configuration

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `create_url` | `bool` | True to show the "Create New" button at the bottom of the dropdown. |
| `resource_type` | `str` | The unique slug matching the registration in the `QuickCreateRegistry`. |
| `choices` | `tuple` | Standard Django choices tuple. Can be passed manually to override. |
| `attrs` | `dict` | Standard HTML attributes (e.g., `id`, `class`). |

---

## 🧩 Technical Details

### DOM Structure (Template)
The widget renders a `searchable-select-container` which contains:
1.  **Selection Button**: Displays the current selection and toggles the dropdown.
2.  **Dropdown Menu**: A hidden `div` containing the search input and result list.
3.  **Hidden Native Select**: A standard `<select>` that holds the actual identity of the value for POST request data.

### JavaScript Logic (`searchable_select.js`)
-   **Filtering**: `filterSearchableOptions()` uses case-insensitive matching against labels.
-   **Dynamic Selection**: `selectSearchableOption()` updates both the visible label and the hidden native select.
-   **Quick Create**: `openQuickCreateModal()` and `submitDynamicQuickCreate()` handle the AJAX lifecycle for new items.
-   **Click-Outside behavior**: Automatically closes dropdowns when clicking anywhere else on the page.

---

## ⚠️ Troubleshooting

-   **Dropdown doesn't open**: Ensure `static/js/searchable_select.js` is loaded and there are no JS errors in the console.
-   **No search results**: Verify the `labels` in your choices aren't empty and that `filterSearchableOptions()` is correctly finding the items.
-   **Quick Create modal doesn't save**: Check if the resource is registered correctly in the registry and that the form validation is passing on the backend.
-   **Z-Index Issues**: If the dropdown is hidden under other elements, check the `z-50` class on the `searchable-dropdown` in the template.

---

*Note: This widget is part of the Profit Pro core-UI system and is the preferred way to handle dynamic select fields.*
