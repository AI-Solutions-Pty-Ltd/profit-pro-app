## Goal
Prevent users from uploading a completely empty Excel sheet (or one where all rows are empty) by detecting this state during upload and returning a clear validation warning/error instead of silently clearing the project's existing BOQ data.

## Constraints
1. Must use Django's validation/errors framework.
2. Must prevent deletion of existing data if the uploaded file is empty.
3. Must remain compatible with single-sheet files and files with a "Setup Template" sheet.
4. Validation should happen in the service layer or form validation layer.

## Known context
- If `import_boq_from_excel` returns `created_count = 0` and `errors = []` (i.e. no parsing errors, but no rows parsed), the database is currently wiped (Structure, Bill, Package, and LineItem are deleted).
- In `import_boq_from_excel`, standard column mapping and empty row checking are already done.
- If all rows are empty, `valid_forms` is empty.

## Risks
- Users who intentionally want to clear all data by uploading an empty sheet won't be able to do so this way. (Mitigation: If they want to clear data, they should use a dedicated "Clear BOQ" button/action in the UI, rather than uploading an empty spreadsheet.)
- We need to make sure we don't accidentally treat a valid sheet with temporary parsing issues (or header matching errors) as "empty" without returning the proper header missing errors. (Mitigation: Check if required columns are missing first, which is already handled and returns specific errors.)

## Options (2–4)
### Option 1: service-level validation in `import_boq_from_excel`
If `len(valid_forms) == 0` after parsing all rows, return `0, ["Excel file is empty. Please ensure it contains at least one valid line item row."]`. This is simple and prevents the deletion transaction from executing since we return an error before the database clear command.

### Option 2: form-level validation in `StructureExcelUploadForm`
Read the Excel file inside the form class's `clean` method and raise a `ValidationError` if the sheet is empty.
- *Pros*: Aligns with Django's standard form validation.
- *Cons*: Re-reads the file twice (once in `clean` and once in `import_boq_from_excel`), which is inefficient and duplicates column normalisation/cleaning code.

### Option 3: service-level check with a custom warning/error flag
Return a specific code or raise an exception when the sheet has 0 data rows, letting the view decide how to handle it (e.g. show a specific modal or warning message instead of a standard form error).

## Recommendation
**Option 1** is highly recommended. It is simple, extremely safe, avoids parsing/reading the file multiple times, and directly prevents data deletion in a single place without modifying view-level logic.

## Acceptance criteria
1. Uploading a completely empty Excel sheet (or one with only empty/formatted blank rows) returns a validation error: `"Excel file is empty. Please ensure it contains at least one valid line item row."`.
2. Existing BOQ data (Structures, Bills, Line Items) is **not** deleted when an empty file is uploaded.
3. Uploading a valid Excel sheet with data continues to succeed and updates the BOQ correctly.
4. Unit tests are added to verify that:
   - Uploading an empty file returns the correct validation error.
   - Uploading an empty file does not delete existing project database records.
