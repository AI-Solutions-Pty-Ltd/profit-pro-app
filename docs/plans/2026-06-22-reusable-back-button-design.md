# Reusable Back Button Design Document

## Goal
Implement a reusable back button template/partial that allows users to return from ledger views (Advance Payments, Retention, Materials on Site, Escalation) back to the active Payment Certificate Edit view from which they navigated.

## Selected Design: Approach A (Conditional Top Button)
A template partial `ledger/partials/back_to_edit_cerficate.html` will be created to render a clean, white, Tailwind-styled button linking back to the edit certificate page if `cancel_url` is present in the context.

## Proposed Changes

### 1. New Template Partial
Create [back_to_edit_cerficate.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/partials/back_to_edit_cerficate.html):
- Add template logic to render the back button conditional on `cancel_url`.
- Use Tailwind CSS and Heroicons (specifically `arrow-left`).

### 2. Update Ledger List Templates
Modify list templates to include the back button:
- `advance_payment_list.html`
- `retention_list.html`
- `materials_list.html`
- `escalation_list.html`

### 3. Update view logic in `ledger_views.py`
Add `cancel_url` and certificate redirect logic for:
- `MaterialsOnSiteListView`
- `MaterialsOnSiteCreateView`
- `MaterialsOnSiteUpdateView`
- `MaterialsOnSiteDeleteView`

### 4. Preserve Query Params in List Components
Update transaction list templates to pass the certificate ID to transaction Edit views:
- `advance_payment_list_component.html`
- `retention_list_component.html`
- `materials_list_component.html`
- `escalation_list_component.html`

## Verification Plan
1. Navigating to the ledger lists via the Payment Certificate Edit page should show the "Back to Edit Certificate" button.
2. Clicking "Back to Edit Certificate" redirects to the correct certificate edit view.
3. Editing a ledger item via the list page and clicking cancel or submitting changes successfully redirects to the certificate edit view.
4. When accessing the list views directly (without `?certificate=...`), the back button is hidden, maintaining proper stand-alone functionality.
