# Design: Remove Excel Unit Dropdown Validation

This design document covers removing the Excel list validation (unit dropdown selection list) from the BOQ template file.

## Requirements
- Target: `app/BillOfQuantities/data/Project set-up Template.xlsx`
- Remove the data validation list associated with the "Unit" column (G2:G1000).
- Preserve all other sheet layouts, styling, notes, formulas, and validations.

## Proposed Changes
We will run a Python script in our development context using `openpyxl` to statically remove the data validation entry that matches the unit list validation.

Specifically:
- Load the workbook `app/BillOfQuantities/data/Project set-up Template.xlsx`.
- Access sheet `Setup Template`.
- Loop over `ws.data_validations.dataValidation`.
- Remove the one with `type == "list"` that governs column G.
- Save the workbook.

## Verification Plan
We will write a test checking that the served/downloaded Excel template indeed has 2 validations (decimal validations on columns H and I) and no unit list validation on column G.
