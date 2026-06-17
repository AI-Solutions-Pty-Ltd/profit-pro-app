# Design: Dynamic File Name Formatting for Project Setup (BOQ)

This document outlines the design for implementing dynamic file name formatting when downloading BOQ templates and uploading/downloading BOQ documents.

## Requirements
- Format: `[Project Name] -project-setup -[Date_Time].[Extension]`
- Date & Time Format: `YYYY-MM-DD_HH-MM-SS` (file-system and header safe)
- Apply to both the BOQ Excel template download and the uploaded BOQ files.

## Proposed Changes

### 1. Template Download Naming
In `app/BillOfQuantities/views/structure_views.py`, modify `DownloadBOQTemplateView` to serve the file with the header set dynamically using the project's name and the current timestamp.
- Get the project name using `self.get_project()`.
- Format timestamp using `timezone.now().strftime("%Y-%m-%d_%H-%M-%S")`.
- Sanitize project name to be filesystem and header-safe (alphanumeric, spaces, underscores, and hyphens only).
- Set `Content-Disposition` response header to `'attachment; filename="[project_name] -project-setup -[timestamp].xlsx"'`.

### 2. Upload File Naming on Filesystem
In `app/Project/documents/document_models.py`, modify `ProjectDocument.upload_to` to format the filename on upload if `self.category` is `BILL_OF_QUANTITIES`.
- Format timestamp using `timezone.now().strftime("%Y-%m-%d_%H-%M-%S")`.
- Rename base filename to: `[project_name] -project-setup -[timestamp].[ext]`.
- This ensures all newly uploaded BOQs are cleanly formatted on the filesystem.

### 3. Secure Media serving Naming
In `app/core/views.py`, modify `serve_media` secure media serving view.
- Intercept downloads of files in `project_documents/<project_id>/BILL_OF_QUANTITIES/`.
- Look up the project and the corresponding `ProjectDocument`.
- Use the document's original `created_at` timestamp (falling back to current time).
- Construct the formatted name and add the `Content-Disposition` header with `attachment; filename="[project_name] -project-setup -[timestamp].[ext]"`.

## Verification Plan

### Automated Tests
- Create tests in `app/BillOfQuantities/tests/test_structure_views.py` verifying template downloads return the correctly formatted filename.
- Create tests in `app/core/tests/test_media_serving.py` verifying BOQ file downloads from media serve correctly format the filename dynamically.
- Verify file uploads naming on saving a new `ProjectDocument` in tests.

### Manual Verification
- Log in, navigate to Project Setup, download the BOQ template, and verify the filename.
- Upload a BOQ file, download it from "View Uploads" or "Recent uploads", and verify the filename is formatted.
