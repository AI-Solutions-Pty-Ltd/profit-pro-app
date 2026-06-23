# Design: Ledger Back to Certificate Edit Functionality

Adding a "Back to Edit Certificate" button next to the "New Transaction" button on all ledger pages.

## Context

Users managing ledger items (Advance Payments, Retention, Materials on Site, Escalation) can access these ledger pages directly or via specific certificate contexts. When visiting these ledger list pages, they need an easy way to go back to the certificate edit page they were working on.

If no specific certificate query parameter is passed in the URL (e.g. `?certificate=43`), the system will automatically fall back to the project's active draft certificate, if one exists.

## Proposed Changes

### Views

#### [MODIFY] [ledger_views.py](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/views/ledger_views.py)
- Update `get_cert_redirect_info` to check if `cert_id` is missing. If missing, look up the active draft payment certificate for the project and use it as a fallback.
- Update `AdvancePaymentListView`, `RetentionListView`, `MaterialsOnSiteListView`, and `EscalationListView` to pass both `cancel_url` and `cert_id` to their contexts.

### Templates

#### [MODIFY] [advance_payment_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/advance_payment_list_component.html)
- Add a "Back to Edit Certificate" button next to "New Transaction" when the component is rendered on the standalone page (i.e. not in the modal on the certificate edit page itself) and `cancel_url` is present.
- Append `?certificate={{ cert_id }}` to the edit and delete links for transactions so the certificate context is maintained when returning.

#### [MODIFY] [retention_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/retention_list_component.html)
- Add the back button next to the "New Transaction" button under the same conditions.
- Append `?certificate={{ cert_id }}` to edit/delete links.

#### [MODIFY] [materials_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/materials_list_component.html)
- Add the back button next to the "New Transaction" button under the same conditions.
- Append `?certificate={{ cert_id }}` to edit/delete links.

#### [MODIFY] [escalation_list_component.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/BillOfQuantities/templates/ledger/components/escalation_list_component.html)
- Add the back button next to the "New Transaction" button under the same conditions.
- Append `?certificate={{ cert_id }}` to edit/delete links.

## Verification Plan

### Automated Tests
- Run `.venv\Scripts\python.exe -m pytest` to ensure no existing tests are broken.
- Write new unit tests or update view tests to verify that `cancel_url` falls back to the active draft certificate and is properly passed to the template contexts.

### Manual Verification
- Verify the "Back to Edit Certificate" button is visible on the standalone ledger pages next to "New Transaction" when an active draft certificate exists.
- Verify the button is NOT visible when viewing the ledger inside the modal on the edit certificate page.
