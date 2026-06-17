# Skip Empty Excel Rows with Formulas on Import Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Ignore/skip empty rows that contain formula defaults (like `Amount = 0.0` or `Rate = 0.0`) during the project BOQ Excel import.

**Architecture:** We will modify the import service in `app/BillOfQuantities/services.py` to check if a row has empty core identifying fields (`Structure`, `Bill No.`, `Item No.`, `Description`). If all are empty, we will skip the row. We will write unit tests for this scenario.

**Tech Stack:** Python, Django, Pytest

---

### Task 1: Modify import BOQ service to skip formula-placeholder empty rows
Update the import logic in `app/BillOfQuantities/services.py`.

**Files:**
- Modify: `app/BillOfQuantities/services.py`
- Test: `app/BillOfQuantities/tests/test_structure_views.py`

**Step 1: Write the failing test**
Add a test case in `app/BillOfQuantities/tests/test_structure_views.py::TestBOQExcelImporter`:

```python
    def test_import_with_partially_empty_formula_rows(self):
        """Test import succeeds and skips empty rows containing formula placeholders (like Amount = 0)."""
        data = [
            {
                "Structure": "Phase 1",
                "Bill No.": "001",
                "Item No.": "1.1",
                "Description": "Trenching",
                "Unit": "m³",
                "Quantity": 10,
                "Rate": 150.0,
                "Amount": 1500.0,
            },
            # Empty row in core fields, but has formula calculation 0.0 in Amount
            {
                "Structure": "",
                "Bill No.": "",
                "Item No.": "",
                "Description": "",
                "Unit": "",
                "Quantity": "",
                "Rate": "",
                "Amount": 0.0,
            },
        ]
        excel_file = self._create_excel_file(data)
        created_count, errors = import_boq_from_excel(self.project, excel_file)

        assert len(errors) == 0
        assert created_count == 1
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py::TestBOQExcelImporter::test_import_with_partially_empty_formula_rows -v`
Expected: FAIL (with validation errors on Structure and Bill No)

**Step 3: Write minimal implementation**
In `app/BillOfQuantities/services.py`, modify `import_boq_from_excel`:
Replace:
```python
            # Skip completely empty rows
            if not any(
                [
                    structure_name,
                    bill_name,
                    package_name,
                    item_number,
                    payment_reference,
                    description,
                    unit_measurement,
                    budgeted_quantity,
                    unit_price,
                    total_price,
                ]
            ):
                continue
```
With:
```python
            # Skip completely empty rows
            if not any(
                [
                    structure_name,
                    bill_name,
                    package_name,
                    item_number,
                    payment_reference,
                    description,
                    unit_measurement,
                    budgeted_quantity,
                    unit_price,
                    total_price,
                ]
            ):
                continue

            # Skip rows where core identifying fields are completely empty (e.g. formula placeholders)
            if not any([structure_name, bill_name, item_number, description]):
                continue
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py::TestBOQExcelImporter::test_import_with_partially_empty_formula_rows -v`
Expected: PASS

**Step 5: Commit**
```bash
git commit -am "feat: skip empty rows containing formula placeholders on Excel import"
```
