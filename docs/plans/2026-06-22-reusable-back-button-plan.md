# Reusable Back Button Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Create a reusable back button to return to the edit certificate page from ledger transaction lists and forms.

**Architecture:** Use a Django template partial `back_to_edit_cerficate.html` that reads `cancel_url` from the context (which is populated by views when navigated from the certificate edit view). Update views and list components to set and preserve this context/query parameter.

**Tech Stack:** Django, Python, HTML/Tailwind CSS, Heroicons.

---

### Task 1: Update Partial Template

**Files:**
- Modify: [back_to_edit_cerficate.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/partials/back_to_edit_cerficate.html)

**Step 1: Write the implementation**
Replace the content of `back_to_edit_cerficate.html` to load heroicons and conditionally render the back button when `cancel_url` is present:
```html
{% load heroicons %}

{% if cancel_url %}
    <div class="mb-4">
        <a href="{{ cancel_url }}"
           class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
            {% heroicon_outline "arrow-left" class="w-4 h-4 mr-2 text-gray-500" %}
            Back to Edit Certificate
        </a>
    </div>
{% endif %}
```

**Step 2: Commit**
Commit changes to git:
```bash
git add app/BillOfQuantities/templates/ledger/partials/back_to_edit_cerficate.html
git commit -m "feat: update back_to_edit_cerficate partial template"
```

---

### Task 2: Include Partial in List Templates

**Files:**
- Modify: [advance_payment_list.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/advance_payment_list.html)
- Modify: [retention_list.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/retention_list.html)
- Modify: [materials_list.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/materials_list.html)
- Modify: [escalation_list.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/escalation_list.html)

**Step 1: Add include tag**
Include `ledger/partials/back_to_edit_cerficate.html` inside the `{% block content %}` before the main list components.

**Step 2: Commit**
```bash
git add app/BillOfQuantities/templates/ledger/*_list.html
git commit -m "feat: include back_to_edit_cerficate in ledger list templates"
```

---

### Task 3: Support `cancel_url` in Materials On Site Views

**Files:**
- Modify: [ledger_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/ledger_views.py)

**Step 1: Add `cancel_url` to `MaterialsOnSite` views**
- In `MaterialsOnSiteListView.get_context_data()`:
  ```python
  _, cancel_url = get_cert_redirect_info(self)
  if cancel_url:
      context["cancel_url"] = cancel_url
  ```
- In `MaterialsOnSiteCreateView.get_context_data()`, `MaterialsOnSiteUpdateView.get_context_data()`, and `MaterialsOnSiteDeleteView.get_context_data()`:
  ```python
  _, cancel_url = get_cert_redirect_info(self)
  if cancel_url:
      context["cancel_url"] = cancel_url
  ```
- In `MaterialsOnSiteCreateView.get_success_url()`, `MaterialsOnSiteUpdateView.get_success_url()`, and `MaterialsOnSiteDeleteView.get_success_url()`:
  ```python
  cert_id, _ = get_cert_redirect_info(self)
  if cert_id:
      return reverse(
          "bill_of_quantities:payment-certificate-edit",
          kwargs={"project_pk": self.kwargs["project_pk"], "pk": cert_id},
      )
  ```

**Step 2: Run pytest to check syntax and errors**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_ledger_views.py -v`

**Step 3: Commit**
```bash
git add app/BillOfQuantities/views/ledger_views.py
git commit -m "feat: add cancel_url and redirect support for materials on site views"
```

---

### Task 4: Add tests for `cancel_url` behavior in ledger views

**Files:**
- Modify: [test_ledger_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_ledger_views.py)

**Step 1: Write test cases**
Add tests to verify that `cancel_url` is added to the context when `certificate` is in the query params.
```python
    def test_materials_list_view_cancel_url(self, client, user, project):
        """Test that materials list view includes cancel_url when certificate is passed."""
        client.force_login(user)
        url = reverse(
            "bill_of_quantities:materials-list", kwargs={"project_pk": project.pk}
        ) + "?certificate=42"
        response = client.get(url)
        assert response.status_code == 200
        assert "cancel_url" in response.context
        assert "payment-certificate-edit" in response.context["cancel_url"]
```

**Step 2: Run pytest**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_ledger_views.py -v`
Expected: PASS

**Step 3: Commit**
```bash
git add app/BillOfQuantities/tests/test_ledger_views.py
git commit -m "test: add cancel_url test cases for ledger list views"
```

---

### Task 5: Preserve Query Params in List Components

**Files:**
- Modify: [advance_payment_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/advance_payment_list_component.html)
- Modify: [retention_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/retention_list_component.html)
- Modify: [materials_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/materials_list_component.html)
- Modify: [escalation_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/escalation_list_component.html)

**Step 1: Append query params to edit and delete URLs**
Change URLs in these templates from:
`{% url '...' project.pk txn.id %}`
To:
`{% url '...' project.pk txn.id %}{% if payment_certificate %}?certificate={{ payment_certificate.id }}{% elif request.GET.certificate %}?certificate={{ request.GET.certificate }}{% endif %}`

**Step 2: Commit**
```bash
git add app/BillOfQuantities/templates/ledger/components/*_list_component.html
git commit -m "feat: preserve certificate query param on edit/delete links"
```

---

### Verification Plan

#### Automated Tests
- Run all ledger views tests:
  `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_ledger_views.py -v`

#### Manual Verification
- Verify the "Back to Edit Certificate" button displays when loading ledger list pages with `?certificate=<id>`.
- Verify the button is NOT shown when navigating to the ledger list pages directly.
- Verify clicking the button returns the user to the correct payment certificate edit page.
