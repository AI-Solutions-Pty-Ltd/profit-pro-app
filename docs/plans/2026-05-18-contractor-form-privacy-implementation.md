# Contractor Form Privacy Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Refactor the Contractor Management edit form to list user names instead of emails, mask sensitive registration and banking info, and allow authorized on-demand decryption using a secure AJAX toggle.

**Architecture:** We use Approach 1: Decrypt-on-demand API with dynamic JS swap. Form fields are masked initially, validation clean methods prevent accidental placeholder database overwrites, and a secure AJAX endpoint reveals plaintext to authorized users.

**Tech Stack:** Python 3.13, Django 5+, Flowbite/Tailwind, Vanilla JS, Pytest.

---

### Task 1: Refactor CompanyForm (Backend logic)

**Files:**
- Modify: `app/Project/company/company_forms.py:28-171`
- Modify: `app/Project/tests/test_forms.py:73-73`

**Step 1: Write the failing tests**
We will append tests inside `app/Project/tests/test_forms.py` verifying that:
1. `CompanyForm` displays human-readable names for `users` selection.
2. Sensitive fields are automatically masked on initialization.
3. Submitting masked values (`••••••••1234`) preserves the original plaintext database values.

```python
    def test_company_form_uses_privacy_user_field(self):
        """Test that the users field represents names instead of emails."""
        from app.Project.company.company_forms import CompanyForm
        form = CompanyForm(contractor=True)
        self.assertEqual(form.fields["users"].queryset.count(), 1)
        # Check label is displayed as name instead of email
        label = form.fields["users"].label_from_instance(self.user)
        self.assertEqual(label, f"{self.user.first_name} {self.user.last_name}")

    def test_company_form_masks_initial_sensitive_data(self):
        """Test that initial sensitive fields are masked to show last 4 chars."""
        from app.Project.company.company_forms import CompanyForm
        company = ClientFactory(
            name="Contractor XYZ",
            type=Company.Type.CONTRACTOR,
            registration_number="1234567890",
            tax_number="TAX-998877",
            vat_number="VAT-776655",
            bank_account_number="9876543210",
            bank_branch_code="198765",
            bank_swift_code="ABSAZAJJ123"
        )
        form = CompanyForm(instance=company, contractor=True)
        self.assertEqual(form.initial["registration_number"], "••••••7890")
        self.assertEqual(form.initial["tax_number"], "••••••8877")
        self.assertEqual(form.initial["bank_swift_code"], "••••••J123")

    def test_company_form_clean_preserves_masked_values(self):
        """Test that submitting a masked value does not overwrite database value."""
        from app.Project.company.company_forms import CompanyForm
        company = ClientFactory(
            name="Contractor XYZ",
            type=Company.Type.CONTRACTOR,
            registration_number="1234567890",
        )
        # Post the masked registration number
        data = {
            "name": "Contractor XYZ",
            "registration_number": "••••••7890",
        }
        form = CompanyForm(data=data, instance=company, contractor=True)
        self.assertTrue(form.is_valid())
        saved_instance = form.save()
        self.assertEqual(saved_instance.registration_number, "1234567890")
```

**Step 2: Run tests to verify they fail**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_forms.py -v`
Expected: FAIL due to missing masking logic and standard email choice labeling.

**Step 3: Implement minimal form code to pass tests**
Modify `app/Project/company/company_forms.py` to:
1. Add `PrivacyModelMultipleChoiceField` class overriding `label_from_instance`.
2. Swap the field class in `CompanyForm` for `users`.
3. Implement `mask_sensitive_value` utility.
4. Update `__init__` to mask initial values for sensitive fields.
5. Add `clean_<field>` methods to ignore submitted values with `•` characters and return database instance values.

**Step 4: Run tests to verify they pass**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_forms.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Project/company/company_forms.py app/Project/tests/test_forms.py
git commit -m "feat: implement contractor form sensitive data masking and user names display"
```

---

### Task 2: Create Secure Reveal AJAX URL & Endpoint

**Files:**
- Modify: `app/Consultant/urls/contractor_management_urls.py:1-40`
- Modify: `app/Consultant/views/contractor_management_views.py:94-150`
- Modify: `app/Consultant/tests/test_contractor_views.py:120-123`

**Step 1: Write the failing tests**
Append test inside `app/Consultant/tests/test_contractor_views.py` verifying:
1. Admin user requests reveal endpoint with valid field -> returns JSON success with plaintext.
2. Unauthorized user requests reveal endpoint -> returns 403 Forbidden.
3. Requesting non-sensitive field returns 400 Bad Request.

```python
    def test_reveal_endpoint_success_for_authorized_user(self):
        """Test that an authorized project admin can retrieve decrypted values."""
        from django.urls import reverse
        import json
        self.client.force_login(self.user)
        # Assuming self.user has Role.ADMIN. Let's create project role
        from app.Project.models import Role, ProjectRole
        ProjectRole.objects.create(project=self.project, user=self.user, role=Role.ADMIN)
        
        url = reverse(
            "client:contractor-management:contractor-reveal-field",
            kwargs={"project_pk": self.project.pk, "company_pk": self.contractor1.pk}
        )
        
        # Add a registration number to the contractor
        self.contractor1.registration_number = "1234567890"
        self.contractor1.save()

        response = self.client.post(
            url,
            data=json.dumps({"field_name": "registration_number"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["value"], "1234567890")
```

**Step 2: Run tests to verify they fail**
Run: `.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_contractor_views.py -v`
Expected: FAIL due to missing URL and View endpoints.

**Step 3: Write minimal implementation**
1. Add route in `app/Consultant/urls/contractor_management_urls.py`.
2. Implement view `RevealContractorFieldView` in `app/Consultant/views/contractor_management_views.py`.

**Step 4: Run tests to verify they pass**
Run: `.venv\Scripts\python.exe -m pytest app/Consultant/tests/test_contractor_views.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add app/Consultant/urls/contractor_management_urls.py app/Consultant/views/contractor_management_views.py app/Consultant/tests/test_contractor_views.py
git commit -m "feat: implement secure on-demand contractor field reveal endpoint"
```

---

### Task 3: Interactive UI (JS overlay swap)

**Files:**
- Modify: `app/Consultant/templates/contractor/contractor_form.html:100-133`

**Step 1: Implement JS script**
Add the Vanilla JS code snippet at the bottom of `contractor_form.html` to convert inputs to read-only state, draw sleek padlock icons overlaying input boxes, and fetch unmasked data asynchronously on click.

**Step 2: Manual Verification**
Start local development server and verify look-and-feel, click behavior, and successful decryption.

**Step 3: Commit**
```bash
git add app/Consultant/templates/contractor/contractor_form.html
git commit -m "feat: wire up interactive front-end lock toggles for secure decryption"
```
