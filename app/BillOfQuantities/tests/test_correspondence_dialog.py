"""Tests for correspondence dialog functionality."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.forms.correspondence_forms import CorrespondenceDialogForm
from app.BillOfQuantities.models.contract_models import (
    CorrespondenceDialog,
    CorrespondenceDialogFile,
)
from app.BillOfQuantities.tests.factories import ContractualCorrespondenceFactory
from app.Project.models import Role
from app.Project.tests.factories import ProjectFactory, ProjectRoleFactory


@pytest.mark.django_db
class TestCorrespondenceDialogModel:
    """Test cases for CorrespondenceDialog model."""

    def test_dialog_creation(self):
        """Test creating a correspondence dialog."""
        correspondence = ContractualCorrespondenceFactory.create()
        sender = AccountFactory.create()
        receiver = AccountFactory.create()

        dialog = CorrespondenceDialog.objects.create(
            correspondence=correspondence,
            sender_user=sender,
            receiver_user=receiver,
            message="Test message",
        )

        assert dialog.id is not None
        assert dialog.correspondence == correspondence
        assert dialog.sender_user == sender
        assert dialog.receiver_user == receiver
        assert dialog.message == "Test message"

    def test_dialog_str(self):
        """Test string representation of dialog."""
        dialog = CorrespondenceDialog.objects.create(
            correspondence=ContractualCorrespondenceFactory.create(),
            message="Test message",
        )
        assert str(dialog).startswith("Dialog for")

    def test_dialog_ordering(self):
        """Test dialogs are ordered by creation date descending."""
        from datetime import timedelta

        from django.utils import timezone

        correspondence = ContractualCorrespondenceFactory.create()

        # Create multiple dialogs with a small delay
        dialog1 = CorrespondenceDialog.objects.create(
            correspondence=correspondence, message="First message"
        )
        # Ensure different creation time
        dialog1.created_at = timezone.now() - timedelta(seconds=1)
        dialog1.save()

        dialog2 = CorrespondenceDialog.objects.create(
            correspondence=correspondence, message="Second message"
        )

        # Query should return newest first
        dialogs = list(CorrespondenceDialog.objects.all())
        assert dialogs[0] == dialog2
        assert dialogs[1] == dialog1

    def test_dialog_with_string_fields(self):
        """Test dialog with string sender/receiver fields."""
        correspondence = ContractualCorrespondenceFactory.create()
        sender = AccountFactory.create()

        dialog = CorrespondenceDialog.objects.create(
            correspondence=correspondence,
            sender_user=sender,
            message="Test message",
            sender="John Doe",
            recipient="Jane Smith",
        )

        assert dialog.sender == "John Doe"
        assert dialog.recipient == "Jane Smith"


@pytest.mark.django_db
class TestCorrespondenceDialogFileModel:
    """Test cases for CorrespondenceDialogFile model."""

    def test_file_creation(self):
        """Test creating a file attachment."""
        dialog = CorrespondenceDialog.objects.create(
            correspondence=ContractualCorrespondenceFactory.create(),
            message="Test message",
        )

        file_content = b"test file content"
        uploaded_file = SimpleUploadedFile(
            "test.pdf", file_content, content_type="application/pdf"
        )

        file_attachment = CorrespondenceDialogFile.objects.create(
            dialog=dialog, file=uploaded_file
        )

        assert file_attachment.id is not None
        assert file_attachment.dialog == dialog
        # Check that "test" and "pdf" are in the filename (Django may add random suffix)
        filename = file_attachment.file.name
        assert "test" in filename and filename.endswith(".pdf")

    def test_file_str(self):
        """Test string representation of file attachment."""
        dialog = CorrespondenceDialog.objects.create(
            correspondence=ContractualCorrespondenceFactory.create(),
            message="Test message",
        )

        file_content = b"test file content"
        uploaded_file = SimpleUploadedFile(
            "test_document.pdf", file_content, content_type="application/pdf"
        )

        file_attachment = CorrespondenceDialogFile.objects.create(
            dialog=dialog, file=uploaded_file
        )

        assert str(file_attachment).startswith("test_document")
        assert str(file_attachment).endswith(".pdf")

    def test_file_ordering(self):
        """Test files are ordered by creation date descending."""
        dialog = CorrespondenceDialog.objects.create(
            correspondence=ContractualCorrespondenceFactory.create(),
            message="Test message",
        )

        # Create multiple files
        file1 = CorrespondenceDialogFile.objects.create(
            dialog=dialog, file=SimpleUploadedFile("file1.pdf", b"content1")
        )
        file2 = CorrespondenceDialogFile.objects.create(
            dialog=dialog, file=SimpleUploadedFile("file2.pdf", b"content2")
        )

        # Query should return newest first
        files = list(CorrespondenceDialogFile.objects.all())
        assert files[0] == file2
        assert files[1] == file1


@pytest.mark.django_db
class TestCorrespondenceForm:
    """Test cases for CorrespondenceForm."""

    def test_form_valid_data(self):
        """Test form with valid data."""
        form_data = {"message": "This is a test message"}
        form = CorrespondenceDialogForm(data=form_data)

        assert form.is_valid()

    def test_form_missing_message(self):
        """Test form without message."""
        form_data = {}
        form = CorrespondenceDialogForm(data=form_data)

        assert not form.is_valid()
        assert "message" in form.errors

    def test_form_with_attachments(self):
        """Test form with file attachments."""
        form_data = {"message": "Test message with attachments"}
        file_data = {
            "attachments": [
                SimpleUploadedFile("file1.pdf", b"content1"),
                SimpleUploadedFile("file2.pdf", b"content2"),
            ]
        }

        form = CorrespondenceDialogForm(data=form_data, files=file_data)

        assert form.is_valid()
        assert len(form.cleaned_data["attachments"]) == 2

    def test_form_save_creates_dialog(self):
        """Test saving form creates dialog."""
        correspondence = ContractualCorrespondenceFactory.create()
        sender = AccountFactory.create()

        form_data = {"message": "Test message"}
        form = CorrespondenceDialogForm(data=form_data)

        assert form.is_valid()

        dialog = form.save(commit=False)
        dialog.correspondence = correspondence
        dialog.sender_user = sender
        dialog.save()

        assert CorrespondenceDialog.objects.count() == 1
        saved_dialog = CorrespondenceDialog.objects.first()
        assert saved_dialog is not None
        assert saved_dialog.message == "Test message"
        assert saved_dialog.sender_user == sender

    def test_form_save_with_attachments(self):
        """Test saving form with attachments creates file objects."""
        correspondence = ContractualCorrespondenceFactory.create()
        sender = AccountFactory.create()

        form_data = {"message": "Test message with attachments"}
        file_data = {
            "attachments": [
                SimpleUploadedFile("file1.pdf", b"content1"),
                SimpleUploadedFile("file2.pdf", b"content2"),
            ]
        }

        form = CorrespondenceDialogForm(data=form_data, files=file_data)

        assert form.is_valid()

        dialog = form.save(commit=False)
        dialog.correspondence = correspondence
        dialog.sender_user = sender
        dialog.save()

        # Manually handle attachments since we used commit=False
        attachments = form.cleaned_data.get("attachments", [])
        for file in attachments:
            if file:
                CorrespondenceDialogFile.objects.create(dialog=dialog, file=file)

        assert CorrespondenceDialog.objects.count() == 1
        assert CorrespondenceDialogFile.objects.count() == 2

        saved_dialog = CorrespondenceDialog.objects.first()
        assert saved_dialog is not None
        assert saved_dialog.attachments.count() == 2


@pytest.mark.django_db
class TestCorrespondenceDialogView:
    """Test cases for correspondence dialog view."""

    def test_dialog_view_creates_message(self, client):
        """Test dialog view creates new message."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(project=project)
        sender = project.users.first()
        recipient = AccountFactory.create()

        correspondence.sender_user = sender
        correspondence.recipient_user = recipient
        correspondence.save()

        client.force_login(sender)

        url = reverse(
            "bill_of_quantities:correspondence-dialog",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        form_data = {"message": "New test message"}

        response = client.post(url, data=form_data)

        assert response.status_code == 302

        # Check dialog was created
        assert CorrespondenceDialog.objects.count() == 1
        dialog: CorrespondenceDialog | None = CorrespondenceDialog.objects.first()
        assert dialog is not None
        assert dialog.message == "New test message"
        assert dialog.sender_user == sender
        assert dialog.receiver_user == recipient

    def test_dialog_view_with_attachments(self, client):
        """Test dialog view handles file attachments."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(project=project)
        sender = project.users.first()
        recipient = AccountFactory.create()

        correspondence.sender_user = sender
        correspondence.recipient_user = recipient
        correspondence.save()

        client.force_login(sender)

        url = reverse(
            "bill_of_quantities:correspondence-dialog",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )
        # Create multipart content manually
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="message"\r\n\r\n'
            f"Message with attachments\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="attachments"; filename="test1.pdf"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
            f"content1\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="attachments"; filename="test2.pdf"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
            f"content2\r\n"
            f"--{boundary}--\r\n"
        )

        content_type = f"multipart/form-data; boundary={boundary}"

        response = client.post(url, data=body, content_type=content_type)

        assert response.status_code == 302

        # Check dialog and files were created
        assert CorrespondenceDialog.objects.count() == 1
        assert CorrespondenceDialogFile.objects.count() == 2

    def test_dialog_view_sets_sender_if_missing(self, client):
        """Test dialog view sets sender_user if not set."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(
            project=project, sender_user=None, sender="Original Sender"
        )
        user = project.users.first()

        client.force_login(user)

        url = reverse(
            "bill_of_quantities:correspondence-dialog",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        form_data = {"message": "Test message"}

        response = client.post(url, data=form_data)

        assert response.status_code == 302

        # Check sender was set
        correspondence.refresh_from_db()
        assert correspondence.sender_user == user

    def test_dialog_view_handles_receiver_logic(self, client):
        """Test dialog view correctly sets receiver based on user."""
        project = ProjectFactory.create()
        sender = project.users.first()
        recipient = AccountFactory.create()
        ProjectRoleFactory.create(project=project, user=recipient, role=Role.ADMIN)

        # Test when user is recipient
        correspondence = ContractualCorrespondenceFactory.create(
            project=project, sender_user=sender, recipient_user=recipient
        )

        client.force_login(recipient)

        url = reverse(
            "bill_of_quantities:correspondence-dialog",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        form_data = {"message": "Reply message"}

        response = client.post(url, data=form_data)

        assert response.status_code == 302

        dialog: CorrespondenceDialog | None = CorrespondenceDialog.objects.first()
        assert dialog is not None
        assert dialog.sender_user == recipient
        assert dialog.receiver_user == sender

    def test_dialog_view_invalid_form(self, client):
        """Test dialog view handles invalid form."""
        project = ProjectFactory.create()
        correspondence = ContractualCorrespondenceFactory.create(project=project)
        user = AccountFactory.create()

        client.force_login(user)

        url = reverse(
            "bill_of_quantities:correspondence-dialog",
            kwargs={"project_pk": project.pk, "pk": correspondence.pk},
        )

        # Empty form should be invalid
        response = client.post(url, data={})

        assert response.status_code == 302
        assert CorrespondenceDialog.objects.count() == 0
