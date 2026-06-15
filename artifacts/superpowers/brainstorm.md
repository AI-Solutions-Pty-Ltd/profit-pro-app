# Superpowers Brainstorm: Contractual Special Items Table Modification

## Goal
Modify the "Contractual Special Items" section in the Payment Certificate pages to render special line items in a detailed 9-column table matching the "Contract Line Items" table structure, including:
- Item No.
- Description
- Price/Unit
- Total Quantity
- Previous Quantity
- Current Quantity
- Total Claimed
- Previous Claim
- Current Claim
- A total row at the bottom summing the current claim values.

## Constraints
- Must inherit and display fields from the annotated `LineItem` instances where `special_item=True` and `addendum=False`.
- Must support all 9 columns and ensure fields display with appropriate styling (like currency formatting and decimal points).
- Must include a total row.
- Must ensure consistent styling (matching `line_items.html` look & feel) across all pages rendering this table:
  - `payment_certificate_detail.html`
  - `payment_certificate_submit.html`
  - `payment_certificate_final_approval.html`
  - `view_detailed.html`
- Resolving the label confusion in `payment_certificate_detail.html` where "Contractual Special Items" is used as the header for ledger totals (which should be named "Ledger Totals"), while actual special line items are not displayed with a visible header (the header is commented out).

## Known context
- Special line items are retrieved as `LineItem` querysets.
- The shared template `app/BillOfQuantities/templates/payment_certificate/tables/special_items.html` is used to render special items.
- Line items are annotated via `LineItem.construct_payment_certificate` with fields: `item_number`, `description`, `unit_price`, `unit_measurement`, `total_qty`, `previous_qty`, `current_qty`, `total_claimed`, `previous_claimed`, and `current_claim`.
- In `payment_certificate_detail.html`:
  - `#special-items` renders `special_items.html` (the header is currently commented out).
  - `#ledger-totals` renders `ledger_totals.html` under the header "Contractual Special Items".
- In `view_detailed.html`:
  - `#special-items` renders `special_items.html` under the header "Special Items".
  - `#ledger-totals` renders `ledger_totals.html` under the header "Ledger Totals".

## Risks
- **Column Overflow on Small Screens**: Displaying 9 columns can cause overflow on narrow viewports.
  - *Mitigation*: Wrap the table in a container with the `overflow-x-auto` utility class.
- **Header Confusions / Broken Layouts**: Renaming headers might confuse users if not done consistently.
  - *Mitigation*: Keep terminology consistent. Rename the header above `ledger_totals.html` to "Ledger Totals" and the header above `special_items.html` to "Contractual Special Items".

## Options (2–4)
### Option 1: Modify the Shared Table Template and Update Headers (Recommended)
Update the shared `special_items.html` table to use a 9-column structure identical to `line_items.html` using the existing annotated attributes of `LineItem`. In `payment_certificate_detail.html`, uncomment the `#special-items` header, name it "Contractual Special Items", and rename the `#ledger-totals` header to "Ledger Totals" to match the layout in `view_detailed.html`.
- *Pros*: Completely DRY, updates all read-only views consistently, resolves header naming bugs, matches existing design patterns.
- *Cons*: None.

### Option 2: Duplicate Template and Create a New Detailed Table for Specific Views
Create a new template file (e.g. `special_items_detailed.html`) specifically for the 9-column view, and only reference it in `payment_certificate_detail.html`, leaving other pages with the 4-column layout.
- *Pros*: Minimal risk of changing other views.
- *Cons*: Code duplication and inconsistent UX across different payment certificate views.

## Recommendation
We recommend **Option 1**. It maintains a single source of truth for rendering special items in read-only views, matches the structure of normal line items, and unifies the headers to resolve layout bugs.

## Acceptance criteria
1. The table rendering `special_line_items` (in `special_items.html`) has 9 columns: `Item No.`, `Description`, `Price/Unit`, `Total Quantity`, `Previous Quantity`, `Current Quantity`, `Total Claimed`, `Previous Claim`, `Current Claim`.
2. A total row is present at the bottom of the table, displaying the total current claim amount of special items.
3. In `payment_certificate_detail.html`, the header for `#special-items` is uncommented and renamed to "Contractual Special Items", and the header for `#ledger-totals` is renamed to "Ledger Totals".
4. The styling (header colors, text alignment, fonts) matches the "Contract Line Items" table styling exactly.
5. All tests pass successfully.
