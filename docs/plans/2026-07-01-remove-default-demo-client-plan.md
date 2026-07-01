# Remove Default Demo Client Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Remove the global default "Demo Client" company (with registration number `DEMO-CLIENT`) from the consultant approval list and client forms for users on the Demo subscription tier.

**Architecture:** We will modify `ConsultantMixin.get_clients()` to remove the `Q(name="Demo Client")` filter. We will modify `ProjectClientForm` and `ProjectFilterForm` to remove `"DEMO-CLIENT"` from their list of allowed registration numbers, keeping only the user-scoped `f"DEMO-CLIENT-{user.pk}"` company.

**Tech Stack:** Django, pytest, factory_boy.

---

### Task 1: Update ConsultantMixin and Test

**Files:**
- Modify: `app/Consultant/views/mixins.py:20-35`
- Test: `app/Consultant/tests/test_demo_tier_consultant.py`

**Step 1: Write the failing test**
In `app/Consultant/tests/test_demo_tier_consultant.py`, add a test to verify that the global "Demo Client" is not returned for active demo users unless explicitly associated:
```python
    def test_consultant_mixin_does_not_return_global_demo_client_by_default(self):
        """Test that ConsultantMixin.get_clients does not include global Demo Client if not associated."""
        global_demo_client = ClientFactory(name="Demo Client", type=Company.Type.CLIENT)
        mixin = ConsultantMixin()
        request = self.factory.get("/")
        request.user = self.demo_user
        mixin.request = request

        clients = mixin.get_clients()
        self.assertNotIn(global_demo_client, list(clients))
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_demo_tier_consultant.py::TestDemoTierConsultantAccess::test_consultant_mixin_does_not_return_global_demo_client_by_default -v`
Expected: FAIL (assertion fails or `global_demo_client` is returned in list)

**Step 3: Write minimal implementation**
In `app/Consultant/views/mixins.py`, update `get_clients` by removing `| Q(name="Demo Client")`:
```python
    def get_clients(self):
        companies = Company.objects.filter(type=Company.Type.CLIENT)
        if not self.request.user.is_superuser:  # type: ignore
            # Allow active DEMO_TIER users to see only their associated or demo client companies
            if getattr(self.request.user, "has_demo_permission", False):
                companies = companies.filter(
                    Q(consultants=self.request.user)
                    | Q(users=self.request.user)
                    | Q(client_projects__in=self.request.user.get_projects)
                ).distinct()
            else:
                companies = companies.filter(
                    consultants=self.request.user,
                )
        return companies
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_demo_tier_consultant.py -v`
Expected: PASS (all tests pass)

**Step 5: Commit**
```bash
git add app/Consultant/views/mixins.py app/Consultant/tests/test_demo_tier_consultant.py
git commit -m "refactor: remove global default demo client from ConsultantMixin"
```

---

### Task 2: Update ProjectClientForm and Test

**Files:**
- Modify: `app/Consultant/forms.py:65-79`
- Test: `app/Project/tests/test_demo_companies.py`

**Step 1: Write the failing test**
In `app/Project/tests/test_demo_companies.py`, update `test_project_client_form_filters_correctly` to assert that the global "Demo Client" is NOT returned in the queryset for active demo users:
```python
    def test_project_client_form_filters_correctly(self):
        """Test that ProjectClientForm filters clients based on user demo permissions."""
        # Case A: Active demo user should see their own user-scoped Demo Client
        form_demo = ProjectClientForm(user=self.demo_user)
        queryset_demo = form_demo.fields["client"].queryset
        expected_name = f"{self.demo_user.first_name}'s Demo Client"
        assert queryset_demo.filter(name=expected_name).exists()
        # ASSERT GLOBAL DEMO CLIENT IS NOT INCLUDED:
        assert not queryset_demo.filter(name="Demo Client").exists()
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_demo_companies.py::TestDemoCompaniesFormFiltering::test_project_client_form_filters_correctly -v`
Expected: FAIL (the global "Demo Client" is present in the queryset)

**Step 3: Write minimal implementation**
In `app/Consultant/forms.py`, update `ProjectClientForm` query condition in `__init__` to exclude `"DEMO-CLIENT"`:
```python
            condition = Q(client_projects__in=projects) | Q(users=user)
            if user.has_demo_permission:
                condition |= Q(
                    registration_number__in=[f"DEMO-CLIENT-{user.pk}"]
                )
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_demo_companies.py::TestDemoCompaniesFormFiltering::test_project_client_form_filters_correctly -v`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Consultant/forms.py app/Project/tests/test_demo_companies.py
git commit -m "refactor: remove global default demo client from ProjectClientForm"
```

---

### Task 3: Update ProjectFilterForm and Test

**Files:**
- Modify: `app/Project/projects/project_forms.py:315-326`
- Test: `app/Project/tests/test_demo_companies.py`

**Step 1: Write the failing test**
In `app/Project/tests/test_demo_companies.py`, update `test_project_filter_form_filters_correctly` to assert that the global "Demo Client" is NOT returned for active demo users in `ProjectFilterForm`:
```python
        # Case A: Active demo user should see both standard and demo companies in ProjectFilterForm
        form_demo = ProjectFilterForm(
            user=self.demo_user,
            client_queryset=client_qs,
            contractor_queryset=contractor_qs,
        )
        expected_client = f"{self.demo_user.first_name}'s Demo Client"
        expected_contractor = f"{self.demo_user.first_name}'s Demo Contractor 1"
        assert form_demo.fields["client"].queryset.filter(name=expected_client).exists()
        assert (
            form_demo.fields["client"].queryset.filter(name="Regular Client").exists()
        )
        # ASSERT GLOBAL DEMO CLIENT IS NOT INCLUDED:
        assert (
            not form_demo.fields["client"]
            .queryset.filter(name="Demo Client")
            .exists()
        )
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_demo_companies.py::TestDemoCompaniesFormFiltering::test_project_filter_form_filters_correctly -v`
Expected: FAIL (the global "Demo Client" is present in the queryset)

**Step 3: Write minimal implementation**
In `app/Project/projects/project_forms.py`, update `ProjectFilterForm`'s `demo_clients` filter to only look for the user-scoped demo client:
```python
        if client_queryset is not None:
            if user and getattr(user, "has_demo_permission", False):
                demo_clients = Company.objects.filter(
                    type=Company.Type.CLIENT,
                    registration_number__in=[f"DEMO-CLIENT-{user.pk}"],
                )
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_demo_companies.py -v`
Expected: PASS (all tests pass)

**Step 5: Commit**
```bash
git add app/Project/projects/project_forms.py app/Project/tests/test_demo_companies.py
git commit -m "refactor: remove global default demo client from ProjectFilterForm"
```
