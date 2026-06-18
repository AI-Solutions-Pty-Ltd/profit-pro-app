## Goal
- Remove the hierarchical grouping by Bill in the Sections list dropdown, and replace it with a flat table display containing all line items of the structure, featuring columns: `ITEM NO.`, `PAY REF`, `DESCRIPTION`, and `TOTAL (R)`.

## Constraints
- **Tech Stack**: Django templates, Tailwind CSS.
- **Visuals**: Clean flat table style with bold headers matching the provided image style (`ITEM NO.`, `PAY REF`, `DESCRIPTION`).
- **Default State**: Keep the default state expanded (using `open` attribute on `<details>`).

## Known context
- File to modify: `app/BillOfQuantities/templates/structure/structure_list.html`.
- Current code groups line items under their respective Bills.
- `LineItem` has fields `item_number`, `payment_reference`, `description`, `total_price`, and `is_work`.

## Risks
- **Table width / overflow**: Since the table will have multiple columns, it must fit inside the list layout without overflowing. Mitigated by using responsive table classes (`overflow-x-auto`) and clean padding.

## Options (2???4)

### Option 1: Clean Tailwind CSS Flat Table (Recommended)
Render the list of line items as a flat HTML table inside the `<details>` dropdown, with explicit `ITEM NO.`, `PAY REF`, `DESCRIPTION`, and `TOTAL (R)` headers.
- **Pros**:
  - Exactly fits the user's screenshot layout guidelines.
  - Highly readable and matches professional billing sheets.
- **Cons**:
  - None.
- **Complexity / risk**: Low.

### Option 2: Simple Flat List
Display the line items as a flat text list rather than a table, separated by delimiters.
- **Pros**:
  - Extremely compact.
- **Cons**:
  - Doesn't match the column headers request.
- **Complexity / risk**: Low.

## Recommendation
- **Option 1** is recommended because a structured HTML table is the standard, cleanest way to present column-aligned tabular data, perfectly satisfying the user's headers design.

## Acceptance criteria
- The sections list dropdown contains a flat table displaying all associated line items.
- The table features column headers: `ITEM NO.`, `PAY REF`, `DESCRIPTION`, and `TOTAL (R)`.
- The layout is clean and matches the project's styling.
- Pytest runs and passes.

