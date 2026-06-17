# Dynamic File Name Formatting for Project Setup (BOQ) Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Implement dynamic file name formatting when downloading BOQ templates and uploading/downloading BOQ documents.

**Architecture:** We will modify the template download view to set the Content-Disposition header with the project-specific formatted filename. We will update `ProjectDocument.upload_to` to format the stored file name on upload. Finally, we will intercept secure media requests in `serve_media` for BOQ files to ensure downloaded filenames are dynamically formatted with correct project name and timestamps.

**Tech Stack:** Django, Python

---

### Task 1: Update Download BOQ Template View
Update the template download view to format the downloaded filename dynamically.

**Files:**
- Modify: `app/BillOfQuantities/views/structure_views.py:280-318`
- Test: `app/BillOfQuantities/tests/test_structure_views.py:412-450`

**Step 1: Write the failing test**
In `app/BillOfQuantities/tests/test_structure_views.py`, modify `test_download_success` to assert the filename format is `{project_name} -project-setup -{current_date_time}.xlsx`.

```python
    def test_download_success(self):
        """Test template download succeeds with correct headers and content."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert (
            response["Content-Type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        import re
        content_disp = response["Content-Disposition"]
        match = re.search(r'attachment; filename="(.+?) -project-setup -(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.xlsx"', content_disp)
        assert match is not None
        assert match.group(1) == self.project.name
        assert len(b"".join(response.streaming_content)) > 0
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py::TestDownloadBOQTemplateView::test_download_success -v`
Expected: FAIL (with assertion error matching filename "Project set-up Template.xlsx")

**Step 3: Write minimal implementation**
In `app/BillOfQuantities/views/structure_views.py`, update `DownloadBOQTemplateView.get`:

```python
    def get(self, request, project_pk):
        template_path = (
            Path(__file__).parent.parent / "data" / "Project set-up Template.xlsx"
        )

        if not template_path.exists():
            messages.error(request, "Template file not found.")
            return redirect(
                reverse(
                    "bill_of_quantities:structure-upload",
                    kwargs={"project_pk": project_pk},
                )
            )

        project = self.get_project()
        import datetime
        from django.utils import timezone
        current_date_time = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (" ", "-", "_")).strip()
        filename = f"{safe_project_name} -project-setup -{current_date_time}.xlsx"

        response = FileResponse(open(template_path, "rb"), as_attachment=True)
        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )
        response["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        return response
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/BillOfQuantities/tests/test_structure_views.py::TestDownloadBOQTemplateView::test_download_success -v`
Expected: PASS

**Step 5: Commit**
```bash
git commit -am "feat: format downloaded BOQ template filename dynamically"
```

---

### Task 2: Update ProjectDocument.upload_to for BOQ category
Update the file upload path formatting for BILL_OF_QUANTITIES category.

**Files:**
- Modify: `app/Project/documents/document_models.py:48-54`
- Test: `app/Project/tests/test_models.py` (Wait, let's add or find ProjectDocument test file)

**Step 1: Write the failing test**
Let's add a test to `app/Project/tests/test_models.py` (or verify/create it) that tests `ProjectDocument` file upload naming.
Wait, let's write the test case code.
```python
    def test_project_document_boq_upload_name(self):
        project = ProjectFactory.create(name="Super Project")
        doc = ProjectDocumentFactory.create(
            project=project,
            category=ProjectDocument.DocumentCategory.BILL_OF_QUANTITIES,
            file=factory.django.FileField(filename="my_boq.xlsx")
        )
        import re
        assert re.search(r'Super Project -project-setup -\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.xlsx$', doc.file.name) is not None
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_models.py -v` (specifically the new test)
Expected: FAIL

**Step 3: Write minimal implementation**
In `app/Project/documents/document_models.py`, update `ProjectDocument.upload_to`:

```python
    def upload_to(self, filename: str) -> str:
        """Generate upload path for document files."""
        import os
        from django.utils import timezone

        base_filename = os.path.basename(filename)
        if self.category == self.DocumentCategory.BILL_OF_QUANTITIES:
            ext = os.path.splitext(base_filename)[1]
            date_str = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
            safe_project_name = "".join(c for c in self.project.name if c.isalnum() or c in (" ", "-", "_")).strip()
            base_filename = f"{safe_project_name} -project-setup -{date_str}{ext}"
        return f"project_documents/{self.project.pk}/{self.category}/{base_filename}"
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_models.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git commit -am "feat: format stored filename on upload for BOQ documents"
```

---

### Task 3: Overwrite Filename header in secure media serving for downloads
Add dynamic header formatting to `serve_media` in `app/core/views.py`.

**Files:**
- Modify: `app/core/views.py:255-300`
- Test: `app/core/tests/test_media_serving.py`

**Step 1: Write the failing test**
In `app/core/tests/test_media_serving.py`, write `test_authenticated_boq_download_header`:

```python
    def test_authenticated_boq_download_header(self, client, settings, tmp_path):
        """Authenticated users downloading BOQ files should receive correctly formatted filename header."""
        from app.Project.tests.factories import ProjectDocumentFactory
        import factory
        
        user = AccountFactory()
        project = ProjectFactory(pk=123, name="My Awesome Project")
        ProjectRoleFactory(project=project, user=user, role=Role.USER)

        client.force_login(user)
        settings.MEDIA_ROOT = str(tmp_path)

        doc = ProjectDocumentFactory.create(
            project=project,
            category=Role.BILL_OF_QUANTITIES, # wait, category in ProjectDocument.DocumentCategory is BILL_OF_QUANTITIES
            file=factory.django.FileField(filename="original_file.xlsx")
        )
        # Note: the factory file field creates the file at settings.MEDIA_ROOT / doc.file.name.
        # Let's ensure the file actually exists
        file_path = tmp_path / doc.file.name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(b"dummy boq data")

        response = client.get(f"/media/{doc.file.name}")
        assert response.status_code == 200
        
        content_disp = response["Content-Disposition"]
        import re
        match = re.search(r'attachment; filename="My Awesome Project -project-setup -(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.xlsx"', content_disp)
        assert match is not None
```

**Step 2: Run test to verify it fails**
Run: `.venv\Scripts\python.exe -m pytest app/core/tests/test_media_serving.py -v`
Expected: FAIL (no Content-Disposition header or wrong format)

**Step 3: Write minimal implementation**
In `app/core/views.py`, update `serve_media` implementation:

```python
def serve_media(request, path):
    # ... existing logic ...
    response = serve(request, path, document_root=settings.MEDIA_ROOT)
    
    # Override Content-Disposition header for BILL_OF_QUANTITIES documents
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "project_documents" and parts[2] == "BILL_OF_QUANTITIES":
        try:
            project_id = int(parts[1])
            from app.Project.models import Project, ProjectDocument
            project = Project.objects.filter(pk=project_id, deleted=False).first()
            if project:
                import os
                from django.utils import timezone
                # Try to find the document to use its creation timestamp, fallback to current time
                doc = ProjectDocument.objects.filter(project=project, file=path).first()
                if doc:
                    date_str = doc.created_at.strftime("%Y-%m-%d_%H-%M-%S")
                else:
                    date_str = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
                
                ext = os.path.splitext(parts[-1])[1]
                safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (" ", "-", "_")).strip()
                filename = f"{safe_project_name} -project-setup -{date_str}{ext}"
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
        except Exception:
            pass
            
    return response
```

**Step 4: Run test to verify it passes**
Run: `.venv\Scripts\python.exe -m pytest app/core/tests/test_media_serving.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git commit -am "feat: override content-disposition header for BOQ media downloads"
```
