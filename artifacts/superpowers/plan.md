## Goal
- Remove the hierarchical grouping by Bill in the Sections list dropdown, and replace it with a flat table display containing all line items of the structure, featuring columns: `ITEM NO.`, `PAY REF`, `DESCRIPTION`, and `TOTAL (R)`.

## Assumptions
- The page includes the structures list.
- All line items of the structure can be fetched via `structure.line_items.all`.

## Plan

1. Update Template
   - Files: `app/BillOfQuantities/templates/structure/structure_list.html`
   - Change: Replace the nested list in the `<details>` dropdown with a clean, flat Tailwind table featuring columns: `ITEM NO.`, `PAY REF`, `DESCRIPTION`, and `TOTAL (R)`. Rename the dropdown summary label to "Items".
   - Verify: Check template file layout.

2. Run Tests
   - Files: None
   - Change: Run the full test suite.
   - Verify: Run `.venv\Scripts\python.exe -m pytest` and ensure all tests pass.

## Risks & mitigations
- **Layout sizing**: The table must be responsive to prevent page layout stretching. Mitigated by using an `overflow-x-auto` wrapper and setting columns with sensible formatting/widths.

## Rollback plan
- Revert changes via git: `git checkout app/BillOfQuantities/templates/structure/structure_list.html`.

