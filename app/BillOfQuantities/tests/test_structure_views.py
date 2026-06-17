"""Tests for Structure views."""

import io
from unittest.mock import patch

import pandas as pd
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from app.Account.subscription_config import Subscription
from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import LineItem, Structure
from app.BillOfQuantities.services import import_boq_from_excel
from app.BillOfQuantities.tests.factories import LineItemFactory, StructureFactory
from app.Project.models import ProjectRole, Role
from app.Project.tests.factories import ProjectFactory


class TestStructureListView(TestCase):
    """Test cases for StructureListView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create(
            subscription=Subscription.PAYMENTS_AND_INVOICES
        )
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        # Create test structures
        self.structure1 = StructureFactory.create(
            project=self.project, name="Section A"
        )
        self.structure2 = StructureFactory.create(
            project=self.project, name="Section B"
        )

        self.url = reverse(
            "bill_of_quantities:structure-list", kwargs={"project_pk": self.project.pk}
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible with correct permission."""
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_view_requires_permission(self):
        """Test view requires correct permission."""
        # Change role to one without permission
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        # Should redirect to login page when user doesn't have permission
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_view_shows_project_structures(self):
        """Test view shows structures for the correct project."""
        other_project = ProjectFactory.create()
        other_structure = StructureFactory.create(project=other_project)

        response = self.client.get(self.url)
        assert response.status_code == 200

        structures = response.context["structures"]
        assert self.structure1 in structures
        assert self.structure2 in structures
        assert other_structure not in structures

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_list.html")

    def test_context_data(self):
        """Test context data is correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.context["project"] == self.project

    def test_breadcrumbs(self):
        """Test breadcrumbs are correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["title"] == "Project Management"
        assert breadcrumbs[1]["title"] == "Sections"


class TestStructureDetailView(TestCase):
    """Test cases for StructureDetailView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create(
            subscription=Subscription.PAYMENTS_AND_INVOICES
        )
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        self.structure = StructureFactory.create(
            project=self.project, name="Test Section"
        )
        self.url = reverse(
            "bill_of_quantities:structure-detail",
            kwargs={"project_pk": self.project.pk, "pk": self.structure.pk},
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible with correct permission."""
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_view_requires_permission(self):
        """Test view requires correct permission."""
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        # Should redirect to login page when user doesn't have permission
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_detail.html")

    def test_context_data(self):
        """Test context data is correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.context["structure"] == self.structure
        assert response.context["project"] == self.project

    def test_breadcrumbs(self):
        """Test breadcrumbs are correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["title"] == "Sections"
        assert breadcrumbs[1]["title"] == self.structure.name


class TestStructureUpdateView(TestCase):
    """Test cases for StructureUpdateView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create(
            subscription=Subscription.PAYMENTS_AND_INVOICES
        )
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        self.structure = StructureFactory.create(
            project=self.project, name="Original Section"
        )
        self.url = reverse(
            "bill_of_quantities:structure-update",
            kwargs={"project_pk": self.project.pk, "pk": self.structure.pk},
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible with correct permission."""
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_view_requires_permission(self):
        """Test view requires correct permission."""
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        # Should redirect to login page when user doesn't have permission
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_form.html")

    def test_form_submission_success(self):
        """Test successful form submission."""
        data = {"name": "Updated Section", "description": "Updated description"}
        response = self.client.post(self.url, data)
        assert response.status_code == 302

        # Check object was updated
        self.structure.refresh_from_db()
        assert self.structure.name == "Updated Section"
        assert self.structure.description == "Updated description"

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "Section 'Updated Section' updated successfully!" in str(messages[0])

    def test_success_url(self):
        """Test successful redirect URL."""
        data = {"name": "Updated Section", "description": "Test"}
        response = self.client.post(self.url, data)
        assert response.status_code == 302
        expected_url = reverse(
            "bill_of_quantities:structure-list", kwargs={"project_pk": self.project.pk}
        )
        assert response["Location"] == expected_url

    def test_breadcrumbs(self):
        """Test breadcrumbs are correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["title"] == "Sections"
        assert "Edit" in breadcrumbs[1]["title"]


class TestStructureDeleteView(TestCase):
    """Test cases for StructureDeleteView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create(
            subscription=Subscription.PAYMENTS_AND_INVOICES
        )
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        self.structure = StructureFactory.create(
            project=self.project, name="Section to Delete"
        )
        self.url = reverse(
            "bill_of_quantities:structure-delete",
            kwargs={"project_pk": self.project.pk, "pk": self.structure.pk},
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible with correct permission."""
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_view_requires_permission(self):
        """Test view requires correct permission."""
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        # Should redirect to login page when user doesn't have permission
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_confirm_delete.html")

    def test_deletion_success(self):
        """Test successful deletion."""
        response = self.client.post(self.url)
        assert response.status_code == 302

        # Check object was soft deleted
        try:
            self.structure.refresh_from_db()
            assert self.structure.is_deleted is True
        except Structure.DoesNotExist:
            # Object was actually deleted from database
            pass

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "Section 'Section to Delete' deleted successfully!" in str(messages[0])

    def test_success_url(self):
        """Test successful redirect URL."""
        response = self.client.post(self.url)
        assert response.status_code == 302
        expected_url = reverse(
            "bill_of_quantities:structure-list", kwargs={"project_pk": self.project.pk}
        )
        assert response["Location"] == expected_url

    def test_breadcrumbs(self):
        """Test breadcrumbs are correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["title"] == "Sections"
        assert "Delete" in breadcrumbs[1]["title"]


class TestStructureExcelUploadView(TestCase):
    """Test cases for StructureExcelUploadView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create(
            subscription=Subscription.PAYMENTS_AND_INVOICES
        )
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        self.url = reverse(
            "bill_of_quantities:structure-upload",
            kwargs={"project_pk": self.project.pk},
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible with correct permission."""
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_view_requires_permission(self):
        """Test view requires correct permission."""
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        # Should redirect to login page when user doesn't have permission
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_excel_upload.html")

    def test_context_data(self):
        """Test context data is correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.context["project"] == self.project

    def test_breadcrumbs(self):
        """Test breadcrumbs are correct."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["title"] == "Structures"
        assert breadcrumbs[1]["title"] == "Upload Structures"

    def test_upload_invalid_excel_renders_validation_errors(self):
        """Test uploading an invalid Excel file renders the page with errors."""
        import io

        import pandas as pd
        from django.core.files.uploadedfile import SimpleUploadedFile

        data = [
            {
                "Structure": "Phase 1",
                "Bill No.": "001",
                "Item No.": "1.1",
                "Description": "Trenching",
                "Unit": "m³",
                "Quantity": 10,
                "Rate": 150.0,
                "Amount": 2000.0,  # 10 * 150 = 1500 != 2000, mismatch error!
            }
        ]
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Setup Template", index=False)
        excel_buffer.seek(0)

        uploaded_file = SimpleUploadedFile(
            "invalid_template.xlsx",
            excel_buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Post the invalid file to the upload view
        response = self.client.post(self.url, {"excel_file": uploaded_file})

        # It should return a 200 OK since it failed validation and re-rendered the form
        assert response.status_code == 200
        self.assertTemplateUsed(response, "structure/structure_excel_upload.html")
        assert "upload_errors" in response.context
        assert len(response.context["upload_errors"]) > 0


class TestDownloadBOQTemplateView(TestCase):
    """Test cases for DownloadBOQTemplateView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create(
            subscription=Subscription.PAYMENTS_AND_INVOICES
        )
        self.project = ProjectFactory.create(users=self.user)
        ProjectRole.objects.create(
            user=self.user, project=self.project, role=Role.CONTRACT_BOQ
        )
        self.client.force_login(self.user)

        self.url = reverse(
            "bill_of_quantities:structure-template-download",
            kwargs={"project_pk": self.project.pk},
        )

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

    def test_downloaded_template_has_no_unit_validation(self):
        """Test that the downloaded template does not contain the unit dropdown validation."""
        response = self.client.get(self.url)
        assert response.status_code == 200

        # Load the workbook from the streaming content using openpyxl
        import io
        import openpyxl

        file_content = b"".join(response.streaming_content)
        wb = openpyxl.load_workbook(io.BytesIO(file_content))
        ws = wb["Setup Template"]

        # Ensure we only have 2 validations (the decimals) and NO list validation
        validations = list(ws.data_validations.dataValidation)
        assert len(validations) == 2
        for dv in validations:
            assert dv.type != "list"

    def test_download_requires_permission(self):
        """Test download requires CONTRACT_BOQ role."""
        ProjectRole.objects.filter(user=self.user, project=self.project).update(
            role=Role.USER
        )
        response = self.client.get(self.url)
        assert response.status_code == 302
        assert response["Location"] == "/"

    @patch("pathlib.Path.exists")
    def test_download_missing_file_graceful_error(self, mock_exists):
        """Test missing file is handled gracefully with an error message."""
        mock_exists.return_value = False
        response = self.client.get(self.url)
        assert response.status_code == 302

        expected_url = reverse(
            "bill_of_quantities:structure-upload",
            kwargs={"project_pk": self.project.pk},
        )
        assert response["Location"] == expected_url

        # Check that error message was set
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "Template file not found." in str(messages[0])


class TestBOQExcelImporter(TestCase):
    """Test cases for import_boq_from_excel service tolerances and validations."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create(
            subscription=Subscription.PAYMENTS_AND_INVOICES
        )
        self.project = ProjectFactory.create(users=self.user)

    def _create_excel_file(self, data):
        """Helper to create an in-memory Excel file from a list of dicts."""
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Setup Template", index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def test_import_with_flexible_headers(self):
        """Test import succeeds with varied column header casing, spaces, and periods."""
        data = [
            {
                "structure": "Phase 1",
                "Bill No.": "001",
                "package_name": "PKG-01",  # Matches normalize of "Package"
                "item_no": "1.1",
                "pay ref": "PR-01",  # Matches normalize of "Pay Ref"
                "DESCRIPTION": "Trenching",
                "Unit": "m³",
                "contract_quantity": 10.5,
                "contract rate": 150.0,
                "Contract.Amount": 1575.0,  # 10.5 * 150.0 = 1575.0
            }
        ]
        excel_file = self._create_excel_file(data)
        created_count, errors = import_boq_from_excel(self.project, excel_file)

        assert len(errors) == 0
        assert created_count == 1
        assert Structure.objects.filter(project=self.project, name="Phase 1").exists()

    def test_import_with_missing_optional_columns(self):
        """Test import succeeds and defaults optional columns when missing entirely."""
        data = [
            {
                "Structure": "Phase 2",
                "Bill No.": "002",
                "Item No.": "2.1",
                "Description": "Piling",
                "Unit": "no",
                "Quantity": 5,
                "Rate": 2000.0,
                "Amount": 10000.0,
                # 'Package' and 'Pay Ref' columns are omitted entirely
            }
        ]
        excel_file = self._create_excel_file(data)
        created_count, errors = import_boq_from_excel(self.project, excel_file)

        assert len(errors) == 0
        assert created_count == 1
        line_item = LineItem.objects.get(description="Piling")
        assert line_item.payment_reference == ""  # Defaulted
        assert line_item.package is None  # Defaulted

    def test_import_calculation_mismatch_fails(self):
        """Test import fails if Contract Amount deviates from Qty * Rate by more than $0.05."""
        data = [
            {
                "Structure": "Phase 3",
                "Bill No.": "003",
                "Item No.": "3.1",
                "Description": "Slab Pouring",
                "Unit": "m²",
                "Contract Quantity": 100,
                "Contract Rate": 350.00,
                "Contract Amount": 35010.00,  # 100 * 350 = 35000, 35010 is mismatch by $10
            }
        ]
        excel_file = self._create_excel_file(data)
        created_count, errors = import_boq_from_excel(self.project, excel_file)

        assert created_count == 0
        assert len(errors) == 1
        assert "Calculation mismatch" in errors[0]

    def test_import_with_empty_rows(self):
        """Test import succeeds and skips completely empty rows (even if extra columns have data)."""
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
                "ExtraCol": 1.0,
            },
            # Empty row for standard columns, but has value in ExtraCol
            {
                "Structure": "",
                "Bill No.": None,
                "Item No.": float("nan"),
                "Description": "",
                "Unit": None,
                "Quantity": None,
                "Rate": None,
                "Amount": None,
                "ExtraCol": 1.0,
            },
        ]
        excel_file = self._create_excel_file(data)
        created_count, errors = import_boq_from_excel(self.project, excel_file)

        # It should succeed because the empty row is skipped!
        assert len(errors) == 0
        assert created_count == 1

    def test_import_empty_file_returns_error_and_does_not_delete(self):
        """Test import fails if Excel file contains no valid line item rows, and existing data is kept."""
        # 1. Create existing structure and line item
        structure = StructureFactory.create(
            project=self.project, name="Existing Structure"
        )
        LineItemFactory.create(
            project=self.project,
            structure=structure,
            description="Existing Line Item",
        )

        # Confirm database has the data
        assert Structure.objects.filter(project=self.project).count() == 1
        assert LineItem.objects.filter(project=self.project).count() == 1

        # 2. Prepare an empty excel file (only headers or formatted empty rows)
        data = [
            {
                "Structure": "",
                "Bill No.": None,
                "Item No.": float("nan"),
                "Description": "",
                "Unit": None,
                "Quantity": None,
                "Rate": None,
                "Amount": None,
                "ExtraCol": 1.0,
            }
        ]
        excel_file = self._create_excel_file(data)

        # 3. Try to import
        created_count, errors = import_boq_from_excel(self.project, excel_file)

        # 4. Assertions
        assert created_count == 0
        assert len(errors) == 1
        assert "Excel file is empty" in errors[0]

        # Confirm database STILL has the original data and has NOT been cleared/deleted
        assert Structure.objects.filter(project=self.project).count() == 1
        assert LineItem.objects.filter(project=self.project).count() == 1
