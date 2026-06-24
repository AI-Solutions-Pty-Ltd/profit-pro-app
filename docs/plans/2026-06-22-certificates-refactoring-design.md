# Design Document: Certificate System Refactoring and Improvements

This document outlines the design and implementation details for the 8 final touch items requested for the Payment Certificates module.

## 1. Include Contractual Special Items in PDF Summary and Excel Exports

### Summary PDF Download (`2-summary.html`)
We will add a new "Contractual Special Items" section to the landscape Valuation Summary PDF template.
* If `payment_certificate.has_contractual_special_items` is true, a table will be appended after a page-break.
* The table will mirror the layout in `3-detailed.html`, showing columns: Description, Previous Amount, Current Amount, and Total Amount, with subtotals for Addendums, Special Items, and Ledger Items (if present), and a Grand Total for Contractual Special Items.

### Excel Export (`detailed_report_exporter.py` / `summary_report_exporter.py`)
* The Detailed Excel Exporter already has a dedicated "Special Items" sheet. We will ensure calculations and rendering align with the PDF detailed report.
* The Summary Excel Exporter already prints special items inline. We will implement formatting changes (detailed in Section 5) to clean up headers and subtotals.

---

## 2. Abridged and Full PDF/XLSX Downloads Bypass for Default Selections

To resolve slow download speeds:
* The default action for downloading PDF and XLSX from the certificate detail/dashboard is to check all three checkboxes (`front`, `summary`, `detailed`).
* When all three default checkboxes are checked, and the request is not forcing regeneration (`force` query param is absent or false), we will skip the on-the-fly synchronous compilation and serve the pre-generated background files (`payment_certificate.pdf`, `payment_certificate.abridged_pdf`, `payment_certificate.xlsx`, `payment_certificate.abridged_xlsx`) directly.
* This will be applied to:
  * `PaymentCertificateDownloadPDFView`
  * `PaymentCertificateDownloadAbridgedPDFView`
  * `PaymentCertificateDownloadUnifiedXLSXView`
  * `PaymentCertificateDownloadUnifiedAbridgedXLSXView`

---

## 3. PDF Summary Title Update

* In `2-summary.html`, the page title/header `<div class="center-box">...` will be renamed from `BILL OF QUANTITIES — SUMMARY` to `VALUATION SUMMARY`.

---

## 4. Valuation Summary BOQ/Bill Natural Sorting

* We will implement a natural sorting helper (`natural_key`) in `app/BillOfQuantities/tasks.py`.
* In `get_valuation_summary_data()`, the dictionary elements representing bills will extract and store `bill_number` from the database `Bill` model.
* Sorting of bills inside sections will change from:
  ```python
  sorted_bills = sorted(s_data["bills"].values(), key=lambda b: b["name"])
  ```
  to:
  ```python
  sorted_bills = sorted(s_data["bills"].values(), key=lambda b: (natural_key(b["bill_number"]), b["name"]))
  ```
* This ensures bills list naturally (e.g., "Bill 2" before "Bill 10").

---

## 5. Excel Valuation Summary Export Cleanup

In `summary_report_exporter.py` under the special items block:
* **a. Remove "Ledger Totals" sub-header**: Do not write the row with value `"Ledger Totals"` below Contractual Special Items.
* **b. Normal Sentence 'Other'**: Map choices from `SpecialItemType` in `get_ledger_summary_items` in `payment_certificate_models.py` to retrieve display labels (e.g., `"Other"` instead of database value `"OTHER"`).
* **c. Rename Subtotal Work Done**: Change cell value from `"SUBTOTAL WORK DONE"` to `"TOTAL WORK DONE TO DATE"`.
* **d. Remove "Subtotal Ledger Items"**: Do not write the ledger subtotal row.

---

## 6. Zeros Exclusion on Heading Rows (`is_work=False`)

* **In-Browser/HTML line items table (`tables/line_items.html`)**:
  Wrap numeric/amount fields in a conditional `{% if line_item.is_work %}` block so that headings (non-work items) remain completely blank in the table columns. If `is_work` is False, render description cell span (`colspan="9"`) like the PDF template, or just blank out the cells. We will use `colspan="9"` to render headings styled as a nice clean banner spanning the table.
* **Excel Exporter (`detailed_report_exporter.py`)**:
  In standard contract items, addendums, and special items loops: if `item.is_work` is False, set all numeric/amount values in `val_map` or written cells to `None` (resulting in blank cells in Excel).

---

## 7. Context-Aware Back Buttons and Redirects for Ledger Forms

* When editing/adding/deleting ledger transactions (Advance Payments, Retention, Materials on Site, Escalation, Special Item Transactions), if a payment certificate context is active:
  * Cancel/back buttons must navigate to the certificate edit page (`payment-certificate-edit`).
  * On success, form submissions and deletions must redirect back to the certificate edit page instead of the general transaction list.
* Implement this in views by checking for `payment_certificate` on the transaction object or checking the presence of a `payment_certificate_id` query parameter (passing it through links in `payment_certificate_edit.html` modals).
* Correct JS action in `special_item_confirm_delete_modal.html` to point to `/bill-of-quantities/...` instead of `/projects/...`.
* Create `ledger/special_item_confirm_delete.html` template.

---

## 8. Remove Bottom Action Links from Certificate Edit Mode

* In `payment_certificate_edit.html`, remove the `Add Addendum Item` button and the `Add Special Item` button at the bottom of the page that show in the empty states.
