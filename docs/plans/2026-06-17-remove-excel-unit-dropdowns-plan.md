# Remove Excel Unit Dropdown Validation Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Remove the unit selection dropdown data validation from the BOQ template excel file.

**Architecture:** We will run a python script to statically strip the validation from the template spreadsheet. We will also add a test to the unit test suite verifying that the downloaded file contains the remaining validations but does not have the list validation.

**Tech Stack:** Python, openpyxl, django-test

---

### Task 1: Statically Remove List Validation from Excel Template
Remove the list validation from the Excel template file.

**Files:**
- Modify: `app/BillOfQuantities/data/Project set-up Template.xlsx` (binary edit via script)

**Step 1: Write a python script to execute the modification**
We will create a python script `app/BillOfQuantities/data/remove_validation.py` to remove the list validation.

```python
import openpyxl

file_path = "app/BillOfQuantities/data/Project set-up Template.xlsx"
wb = openpyxl.load_workbook(file_path)
ws = wb["Setup Template"]

to_remove = None
for dv in ws.data_validations.dataValidation:
    if dv.type == "list" and "sum" in str(dv.formula1):
        to_remove = dv
        break

if to_remove:
    ws.data_validations.dataValidation.remove(to_remove)
    wb.save(file_path)
    print("Successfully removed list validation.")
else:
    print("List validation not found.")
```

**Step 2: Run the script to modify the template**
Run: `.venv\Scripts\python.exe -c "import openpyxl; wb=openpyxl.load_workbook('app/BillOfQuantities/data/Project set-up Template.xlsx'); ws=wb['Setup Template']; assert len(ws.data_validations.dataValidation) == 3"` (verify it currently has 3)
Run: `.venv\Scripts\python.exe -c "import openpyxl; file_path='app/BillOfQuantities/data/Project set-up Template.xlsx'; wb=openpyxl.load_workbook(file_path); ws=wb['Setup Template']; [ws.data_validations.dataValidation.remove(dv) for dv in list(ws.data_validations.dataValidation) if dv.type == 'list']; wb.save(file_path)"`
Run verification check: `.venv\Scripts\python.exe -c "import openpyxl; wb=openpyxl.load_workbook('app/BillOfQuantities/data/Project set-up Template.xlsx'); ws=wb['Setup Template']; print(len(ws.data_validations.dataValidation)); assert len(ws.data_validations.dataValidation) == 2"`
Expected: 2 validations left (decimal validations).

**Step 3: Commit the modified template**
```bash
git add app/BillOfQuantities/data/Project set-up Template.xlsx
git commit -m "style/refactor: remove unit dropdown list validation from excel template"
```

---

### Task 2: Add Test to Verify Downloaded Template has no Unit Validation List
Write a test to ensure the served template has the correct validation settings.

**Files:**
- Modify: `app/BillOfQuantities/tests/test_structure_views.py`

**Step 1: Write the failing test**
Add a test in `app/BillOfQuantities/tests/test_structure_views.py::TestDownloadBOQTemplateView`:

```python
    def test_downloaded_template_has_no_unit_validation(self):
        """Test that the downloaded template does not contain the unit dropdown validation."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        
        # Load the workbook from the streaming content using openpyxl
        import openpyxl
        import io
        file_content = b"".join(response.streaming_content)
        wb = openpyxl.load_workbook(io.BytesIO(file_content))
        ws = wb["Setup Template"]
        
        # Ensure we only have 2 validations (the decimals) and NO list validation
        validations = list(ws.data_validations.dataValidation)
        assert len(validations) == 2
        for dv in validations:
            assert dv.type != "list"
```

**Step 2: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py::TestDownloadBOQTemplateView::test_downloaded_template_has_no_unit_validation -v`
Expected: PASS

**Step 3: Commit**
```bash
git commit -am "test: add verification for removed Excel unit dropdown validation"
```
