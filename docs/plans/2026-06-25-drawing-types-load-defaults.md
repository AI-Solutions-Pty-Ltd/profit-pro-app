# Drawing Types Load Defaults Button Implementation Plan

**Goal:** Add a "Load Defaults" button on the project drawing types register page to automatically populate the 4 default drawing types: Construction, Information, Shop, and Tender.

**Architecture:**
1. Define a list of default drawing types with names and descriptions.
2. Add `DrawingTypeLoadDefaultsView` class to `app/Project/projects/category_views.py`.
3. Register the path in `app/Project/projects/category_urls.py`.
4. Update `app/Project/templates/project/drawing_types/drawing_type_manage.html` to add the "Load Defaults" button and a AJAX call.
5. Add automated tests to verify the behavior.

**Tech Stack:** Django, Tailwind CSS, Javascript Fetch API

---

### Task 1: Create backend view and default drawing types list

**Files:**
- Modify: [category_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/category_views.py)

**Step 1: Define DEFAULT_DRAWING_TYPES**
Define the 4 default drawing types:
```python
DEFAULT_DRAWING_TYPES = [
    {"name": "Construction", "description": "Construction drawing type"},
    {"name": "Information", "description": "Information drawing type"},
    {"name": "Shop", "description": "Shop drawing type"},
    {"name": "Tender", "description": "Tender drawing type"},
]
```

**Step 2: Add DrawingTypeLoadDefaultsView**
Implement the POST endpoint, skipping already existing drawing types (case-insensitive check).

---

### Task 2: Register the URL path

**Files:**
- Modify: [category_urls.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/projects/category_urls.py)

**Step 3: Register path**
Add `project-drawing-type-load-defaults` url pattern.

---

### Task 3: Add button and JS to the template

**Files:**
- Modify: [drawing_type_manage.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/project/drawing_types/drawing_type_manage.html)

**Step 4: Add Load Defaults button in the header**
Add a Teal button similar to the one on the disciplines page.

**Step 5: Add Javascript handling**
Implement the post request using Fetch API with CSRF token support, showing a loading indicator and reloading the page on success.

---

### Task 4: Add automated tests and verify

**Files:**
- Create: [test_drawing_type_defaults.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/tests/test_drawing_type_defaults.py)

**Step 6: Write unit tests**
Verify that the POST endpoint successfully creates all 4 drawing types, skips duplicates case-insensitively, and handles permissions correctly.

**Step 7: Run verification**
Run pytest and linting.
