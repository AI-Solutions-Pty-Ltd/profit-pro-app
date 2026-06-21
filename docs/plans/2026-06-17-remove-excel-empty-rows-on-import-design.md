# Design: Skip Empty Excel Rows with Formulas on Import

This design document covers ignoring/skipping empty rows that contain formula defaults (like `Amount = 0.0`) during the project BOQ Excel/CSV import.

## Requirements
- Target: `app/BillOfQuantities/services.py`
- Avoid importing or raising validation errors for rows that contain no actual BOQ line item data (Structure, Bill, Item No, and Description are all blank) but may contain formula defaults or formatting in other columns.

## Proposed Changes
We will update `import_boq_from_excel` in `app/BillOfQuantities/services.py` to check if the core data fields are all empty:
```python
# Skip rows that don't have any core BOQ data (structure, bill, item_no, description)
if not any([structure_name, bill_name, item_number, description]):
    continue
```
This is placed right after extracting the values and before validating quantities/rates/amounts, ensuring they are silently skipped.

## Verification Plan
- Add a unit test verifying that uploading an Excel file containing rows with `Amount = 0` but no core data correctly ignores those rows and imports successfully.
