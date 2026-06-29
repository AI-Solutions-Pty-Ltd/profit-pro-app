import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from app.Project.models import ProjectRole, Role, ProjectDocument
from app.Project.tests.factories import (
    AccountFactory,
    ProjectFactory,
    ProjectDocumentFactory,
)


@pytest.mark.django_db
class TestDocumentViews:
    """Test cases for Document views."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)
        # Assign user ADMIN role for project permissions
        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )
        self.category = "SPECIFICATIONS"
        self.create_url = reverse(
            "project:document-upload",
            kwargs={"project_pk": self.project.pk, "category": self.category},
        )

    def test_document_create_view_renders(self, client):
        """Test that the document upload form renders correctly."""
        client.force_login(self.user)
        response = client.get(self.create_url)
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Upload Document" in content
        assert "Document Title" in content

    def test_document_create_submission(self, client):
        """Test uploading a new document."""
        client.force_login(self.user)
        uploaded_file = SimpleUploadedFile("spec.pdf", b"file_content", content_type="application/pdf")
        
        post_data = {
            "title": "Project Specification File",
            "file": uploaded_file,
            "notes": "Important specification notes",
            "category": self.category,
        }
        
        response = client.post(self.create_url, data=post_data)
        if response.status_code != 302:
            print("Form errors:", response.context['form'].errors)
        assert response.status_code == 302
        
        # Verify document was created
        doc = ProjectDocument.objects.get(title="Project Specification File")
        assert doc.project == self.project
        assert doc.category == self.category
        assert doc.notes == "Important specification notes"

    def test_document_edit_view_renders(self, client):
        """Test that the document edit form renders correctly."""
        client.force_login(self.user)
        doc = ProjectDocumentFactory(project=self.project, category=self.category, title="Original Title")
        edit_url = reverse(
            "project:document-edit",
            kwargs={"project_pk": self.project.pk, "category": self.category, "pk": doc.pk},
        )
        
        response = client.get(edit_url)
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Edit Document" in content
        assert "Original Title" in content

    def test_document_edit_submission(self, client):
        """Test editing an existing document."""
        client.force_login(self.user)
        doc = ProjectDocumentFactory(project=self.project, category=self.category, title="Original Title")
        edit_url = reverse(
            "project:document-edit",
            kwargs={"project_pk": self.project.pk, "category": self.category, "pk": doc.pk},
        )
        
        post_data = {
            "title": "Updated Title",
            "notes": "Updated notes",
            "category": self.category,
        }
        
        response = client.post(edit_url, data=post_data)
        if response.status_code != 302:
            print("Form errors:", response.context['form'].errors)
        assert response.status_code == 302
        
        # Verify document was updated
        doc.refresh_from_db()
        assert doc.title == "Updated Title"
        assert doc.notes == "Updated notes"

    def test_document_wbs_and_revision_fields(self, client):
        """Test document creation with WBS level and revision number."""
        from app.Project.tests.factories import (
            CategoryFactory,
            SubCategoryFactory,
            GroupFactory,
        )
        
        client.force_login(self.user)
        category_l1 = CategoryFactory(project=self.project, name="Sector L1")
        subcategory_l2 = SubCategoryFactory(category=category_l1, project=self.project, name="Sub L2")
        group_l3 = GroupFactory(sub_category=subcategory_l2, project=self.project, name="Grp L3")
        
        # Test L3 group resolution
        uploaded_file = SimpleUploadedFile("spec.pdf", b"file_content", content_type="application/pdf")
        post_data = {
            "title": "Specs with WBS",
            "file": uploaded_file,
            "document_number": "SPEC-001",
            "revision_number": "B",
            "wbs_level": f"group_{group_l3.pk}",
            "category": self.category,
        }
        
        response = client.post(self.create_url, data=post_data)
        if response.status_code != 302:
            print("Form errors:", response.context['form'].errors)
        assert response.status_code == 302
        
        # Verify fields on the document record
        doc = ProjectDocument.objects.get(title="Specs with WBS")
        assert doc.document_number == "SPEC-001"
        assert doc.revision_number == "B"
        assert doc.project_category == category_l1
        assert doc.sub_category == subcategory_l2
        assert doc.group == group_l3
