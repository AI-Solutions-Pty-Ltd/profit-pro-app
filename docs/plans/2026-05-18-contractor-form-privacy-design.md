# Design Specification: Contractor Form Privacy Enhancements

This specification details the architecture, data protection rules, and interactive user experience for refactoring the Contractor Management form page to introduce high-grade privacy controls.

## Goals
1. **User Names instead of Emails**: Display clear human-readable names (`first_name last_name`) instead of user emails in the company users multi-select checkboxes.
2. **On-Demand Decryption / Masking**: Hide sensitive corporate and banking numbers by default under uniform 4-character masking (`••••••••1234`), providing a secure "Edit/Reveal" dynamic swap triggered by AJAX authorization.

---

## Architectural Approach
We use **Approach 1: Decrypt-on-Demand AJAX API + Dynamic HTML Swap**.
* The initial HTML document rendered by the browser contains only the masked placeholders.
* Sensitive raw strings are *never* transmitted in the standard page source.
* A secure API endpoint checks user permissions before returning the plaintext string.
* Vanilla JS handles visual state transitions, unlocking inputs seamlessly.

---

## Technical Specifications

### 1. Form & User Refactoring (Backend)
* **File**: `app/Project/company/company_forms.py`
* **Custom Field**: Create `PrivacyModelMultipleChoiceField` overriding `label_from_instance` to yield `f"{obj.first_name} {obj.last_name}"`.
* **Masking Util**: Map sensitive fields (`registration_number`, `tax_number`, `vat_number`, `bank_account_number`, `bank_branch_code`, `bank_swift_code`) to mask initial values using uniform `••••` characters showing only the last 4 characters.
* **Overriding Validation**: Prevent overwriting actual data with placeholders by mapping custom clean validators (`clean_<field>`). If the submitted value contains bullet characters (`•`), the clean methods return the original unmasked instance values.

### 2. Decrypt API Endpoint
* **URL Route**: `project/<int:project_pk>/contractor/<int:company_pk>/reveal-field/`
* **Controller**: `RevealContractorFieldView` inside `app/Consultant/views/contractor_management_views.py` inheriting `ContractorMixin` for automatic permission checking (`Role.ADMIN` / superuser). Returns a secure JSON payload with the plaintext value upon POST request.

### 3. Frontend Layout & Interactive JavaScript
* **File**: `app/Consultant/templates/contractor/contractor_form.html`
* **Interface**:
  * Targets the sensitive fields when in **Edit** mode.
  * Inputs start as `readonly bg-gray-100 cursor-not-allowed`.
  * Inject an interactive lock icon overlay. Clicking this icon requests the unmasked value via AJAX, dynamically swaps the value, and changes the icon to a green "unlocked" checkmark while enabling editing.

---

## Verification Plan

### Automated Verification
* Unit tests for `CompanyForm` verifying that submitting masked data does not overwrite database fields with placeholders.
* Unit tests for `RevealContractorFieldView` confirming that unauthorized users receive a 403 Forbidden response.

### Manual Verification
* Inspect the form source code to verify that raw banking details are completely absent from the DOM.
* Verify user selections display names correctly.
