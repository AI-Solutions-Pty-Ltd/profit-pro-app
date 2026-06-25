# Design: System Library Municipalities Register

This document outlines the design to add a new register in the System Library for managing South African provinces and municipalities.

## 1. Objectives
* Add a "Municipalities" register to the System Library to allow staff to manage standard provinces/municipalities.
* Support adding new records, searching/filtering, bulk deletion, clearing all, and importing from Excel.
* Reuse the existing `Account.Municipality` model.

## 2. Architecture & Components

### 2.1 URLs (`app/Estimator/urls.py`)
Add routes:
* `system/municipalities/` -> `SystemMunicipalityListView` (name: `sys_municipalities`)
* `system/municipalities/upload/` -> `SystemMunicipalityUploadView` (name: `sys_municipality_upload`)
* `system/municipalities/template/` -> `DownloadSystemMunicipalityTemplateView` (name: `sys_download_municipality_template`)

### 2.2 Model Form (`app/Estimator/forms.py`)
* Class: `SystemMunicipalityForm`
* Model: `app.Account.models.Municipality`
* Fields: `province`, `municipality_name`, `code`, `district`
* Styles: Styled using `TAILWIND_INPUT` input class.

### 2.3 Views (`app/Estimator/views.py`)
* **`SystemMunicipalityListView`**
  - Requires `is_staff` credentials via `SystemLibraryMixin`.
  - Performs pagination (e.g., 50 items per page).
  - Handles filter by `q` (search) and `province`.
  - Handles POST requests for single addition, bulk deletion, and clearing all.
* **`SystemMunicipalityUploadView`**
  - Uses `ExcelImportForm` and handles Excel uploads using `MunicipalityImporter`.
* **`DownloadSystemMunicipalityTemplateView`**
  - Generates template sheet with columns: `Province`, `Municipality Name`, `Code`, `District`.

### 2.4 Importer (`app/Estimator/importers.py`)
* Class: `MunicipalityImporter`
* Reads uploaded workbook, matches sheet name fuzzily.
* Performs `update_or_create` on `(province, municipality_name, code)`.

### 2.5 Templates
* Add "Municipalities" tab to `app/Estimator/templates/estimator/system/base_system.html`.
* Create `app/Estimator/templates/estimator/system/municipality_list.html` reusing existing layout logic from other library pages.

## 3. Testing & Verification
* Write tests in `app/Estimator/tests/test_system_municipalities.py` verifying:
  - Access control (requires staff).
  - Adding a municipality via the view POST.
  - Search and filter logic.
  - Excel template import and download.
  - Bulk delete and clear all.
