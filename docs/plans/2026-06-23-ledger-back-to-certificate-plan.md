# Ledger Back to Certificate Edit Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Add a "Back to Edit Certificate" button next to "New Transaction" on all ledger lists (Advance Payment, Retention, Materials, Escalation) and support automatic fallback to the project's active draft certificate.

**Architecture:** Update `get_cert_redirect_info` in `app/BillOfQuantities/views/ledger_views.py` to check for active draft certificate if `certificate` is not in URL params. Expose both `cancel_url` and `cert_id` to ledger list views, then update list components to render the back button next to "New Transaction".

**Tech Stack:** Python, Django, HTML, TailwindCSS

---

### Task 1: Write test cases in test_ledger_views.py

**Files:**
- Create: [test_ledger_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/tests/test_ledger_views.py)

**Step 1: Write tests**
Create `app/BillOfQuantities/tests/test_ledger_views.py` with test cases verifying the `cancel_url` and `cert_id` logic.

```python
import pytest
from django.urls import reverse
from app.BillOfQuantities.tests.factories import PaymentCertificateFactory
from app.Project.tests.factories import ProjectFactory, ProjectRoleFactory
from app.Project.models import Role
from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import PaymentCertificate

@pytest.mark.django_db
class TestLedgerViewsCancelUrl:
    """Test cancel_url and cert_id logic in ledger list views."""

    def test_cancel_url_with_query_param(self, client):
        """Should resolve cancel_url and cert_id from query parameter."""
        project = ProjectFactory()
        user = AccountFactory()
        ProjectRoleFactory(project=project, account=user, role=Role.USER)
        cert = PaymentCertificateFactory(project=project, status=PaymentCertificate.Status.DRAFT)
        
        client.force_login(user)
        url = reverse("bill_of_quantities:advance-payment-list", kwargs={"project_pk": project.pk})
        response = client.get(f"{url}?certificate={cert.pk}")
        
        assert response.status_code == 200
        assert response.context["cert_id"] == str(cert.pk)
        assert response.context["cancel_url"] == reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": cert.pk}
        )

    def test_cancel_url_fallback_to_draft(self, client):
        """Should fall back to active draft certificate if query param is absent."""
        project = ProjectFactory()
        user = AccountFactory()
        ProjectRoleFactory(project=project, account=user, role=Role.USER)
        cert = PaymentCertificateFactory(project=project, status=PaymentCertificate.Status.DRAFT)
        
        client.force_login(user)
        url = reverse("bill_of_quantities:advance-payment-list", kwargs={"project_pk": project.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.context["cert_id"] == cert.pk
        assert response.context["cancel_url"] == reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": cert.pk}
        )

    def test_cancel_url_no_fallback_without_draft(self, client):
        """Should set cancel_url to None if query param is absent and no draft certificate exists."""
        project = ProjectFactory()
        user = AccountFactory()
        ProjectRoleFactory(project=project, account=user, role=Role.USER)
        # Payment certificate has APPROVED status (not DRAFT)
        PaymentCertificateFactory(project=project, status=PaymentCertificate.Status.APPROVED)
        
        client.force_login(user)
        url = reverse("bill_of_quantities:advance-payment-list", kwargs={"project_pk": project.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert "cert_id" not in response.context or response.context.get("cert_id") is None
        assert "cancel_url" not in response.context or response.context.get("cancel_url") is None
```

**Step 2: Run test to verify it fails/errors**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_ledger_views.py -v`
Expected: FAIL/error because `cert_id` is not set in the view context, and fallback is not implemented.

**Step 3: Commit initial failing test**
Run:
```bash
git add app/BillOfQuantities/tests/test_ledger_views.py
git commit -m "test: add failing ledger view cancel_url tests"
```

---

### Task 2: Implement cancel_url fallback and cert_id context in views

**Files:**
- Modify: [ledger_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/ledger_views.py)

**Step 1: Implement fallback and return cert_id**
Update `get_cert_redirect_info` in `app/BillOfQuantities/views/ledger_views.py` to:
1. Try fetching from GET/POST request.
2. If missing, fetch from `PaymentCertificate.objects.filter(project_id=project_pk, status=PaymentCertificate.Status.DRAFT).first()`.
3. Return `cert_id, cancel_url`.

Modify the `get_context_data` of the 4 ledger list views:
- `AdvancePaymentListView`
- `RetentionListView`
- `MaterialsOnSiteListView`
- `EscalationListView`

To pass `cert_id` and `cancel_url` to the template context.

**Step 2: Run test to verify they pass**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_ledger_views.py -v`
Expected: PASS

**Step 3: Commit implementation**
Run:
```bash
git add app/BillOfQuantities/views/ledger_views.py
git commit -m "feat: implement active draft certificate fallback and context injection for ledgers"
```

---

### Task 3: Add back button and certificate ID to templates

**Files:**
- Modify: [advance_payment_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/advance_payment_list_component.html)
- Modify: [retention_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/retention_list_component.html)
- Modify: [materials_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/materials_list_component.html)
- Modify: [escalation_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/escalation_list_component.html)

**Step 1: Add back buttons next to New Transaction**
In each component, wrap the "New Transaction" button in a flex container with the back button:
```html
            <div class="flex items-center space-x-3">
                {% if not payment_certificate and cancel_url %}
                    <a href="{{ cancel_url }}"
                       class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
                        {% heroicon_outline "arrow-left" class="w-4 h-4 mr-2 text-gray-500" %}
                        Back to Edit Certificate
                    </a>
                {% endif %}
                <button onclick="openFormModal()" ...>
                    ...
                </button>
            </div>
```
*(adjusting specific button attributes per component)*

**Step 2: Append certificate to actions**
In the transaction table rows, append the certificate query parameter to Edit and Delete actions if `cert_id` or `request.GET.certificate` is present:
`{% if cert_id %}?certificate={{ cert_id }}{% elif request.GET.certificate %}?certificate={{ request.GET.certificate }}{% endif %}`

**Step 3: Run all tests**
Run: `.venv\Scripts\python.exe -m pytest`
Expected: PASS

**Step 4: Commit templates**
Run:
```bash
git add app/BillOfQuantities/templates/ledger/components/
git commit -m "feat: add back to edit certificate buttons next to new transaction and pass certificate context"
```
