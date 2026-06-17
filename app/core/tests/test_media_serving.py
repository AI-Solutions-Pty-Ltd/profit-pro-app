import os
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from app.Account.tests.factories import AccountFactory
from app.Project.models import Role
from app.Project.tests.factories import ProjectFactory, ProjectRoleFactory

User = get_user_model()


@pytest.mark.django_db
class TestMediaServing:
    """Test suite for secure media serving view."""

    def test_unauthenticated_sensitive_access(self, client):
        """Unauthenticated requests to sensitive media files should redirect to login."""
        response = client.get("/media/project_documents/1/some_file.xlsx")
        assert response.status_code == 302
        assert "login" in response.url

    def test_unauthenticated_non_sensitive_access(self, client, settings, tmp_path):
        """Unauthenticated requests to non-sensitive media files (like logos) should be allowed."""
        settings.MEDIA_ROOT = str(tmp_path)

        # Create a dummy logo file
        logo_dir = tmp_path / "project_logos"
        logo_dir.mkdir(parents=True, exist_ok=True)
        logo_file = logo_dir / "logo.png"
        logo_file.write_bytes(b"dummy image data")

        response = client.get("/media/project_logos/logo.png")
        assert response.status_code == 200
        assert b"".join(response.streaming_content) == b"dummy image data"

    def test_authenticated_no_project_access(self, client):
        """Authenticated users without project roles should be denied access (404)."""
        user = AccountFactory()
        client.force_login(user)

        # Create project but do not assign role
        ProjectFactory(pk=999)

        response = client.get("/media/project_documents/999/test.xlsx")
        assert response.status_code == 404

    def test_authenticated_with_project_access(self, client, settings, tmp_path):
        """Authenticated users with valid project roles should be allowed to download project files."""
        user = AccountFactory()
        project = ProjectFactory(pk=123)
        ProjectRoleFactory(project=project, user=user, role=Role.USER)

        client.force_login(user)
        settings.MEDIA_ROOT = str(tmp_path)

        # Create a dummy file in a project subfolder
        doc_dir = tmp_path / "project_documents" / "123"
        doc_dir.mkdir(parents=True, exist_ok=True)
        doc_file = doc_dir / "CONTRACT_DOCUMENTS" / "my_contract.pdf"
        doc_file.parent.mkdir(parents=True, exist_ok=True)
        doc_file.write_bytes(b"dummy pdf data")

        response = client.get("/media/project_documents/123/CONTRACT_DOCUMENTS/my_contract.pdf")
        assert response.status_code == 200
        assert b"".join(response.streaming_content) == b"dummy pdf data"

    def test_authenticated_boq_download_header(self, client, settings, tmp_path):
        """Authenticated users downloading BOQ files should receive correctly formatted filename header."""
        from app.Project.tests.factories import ProjectDocumentFactory
        import factory
        import re

        user = AccountFactory()
        project = ProjectFactory(pk=123, name="My Awesome Project")
        ProjectRoleFactory(project=project, user=user, role=Role.USER)

        client.force_login(user)
        settings.MEDIA_ROOT = str(tmp_path)

        # Create a ProjectDocument in database
        doc = ProjectDocumentFactory.create(
            project=project,
            category="BILL_OF_QUANTITIES",
            file=factory.django.FileField(filename="my_boq.xlsx")
        )

        # Ensure the file actually exists in settings.MEDIA_ROOT / doc.file.name
        file_path = tmp_path / doc.file.name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(b"dummy boq data")

        response = client.get(f"/media/{doc.file.name}")
        assert response.status_code == 200
        assert b"".join(response.streaming_content) == b"dummy boq data"

        content_disp = response.get("Content-Disposition", "")
        # Expect dynamic project setup naming format
        match = re.search(r'attachment; filename="My Awesome Project -project-setup -(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.xlsx"', content_disp)
        assert match is not None

