import pytest
from django.urls import reverse

from app.Project.models.entity_definitions import MaterialEntity
from app.Project.tests.factories import AccountFactory, ProjectFactory


@pytest.mark.django_db
class TestMaterialEntityBulkCreate:
    """Tests for MaterialEntity multi-item creation."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)
        self.url = reverse(
            "project:entity-material-create",
            kwargs={"project_pk": self.project.pk},  # type: ignore
        )

    def test_bulk_create_get(self, client):
        """Test that GET request returns the bulk form with correct context."""
        client.force_login(self.user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert "header_form" in response.context
        assert "formset" in response.context
        assert response.template_name[0] == "entity_management/material_bulk_form.html"

    def test_bulk_create_success(self, client):
        """Test successful creation of multiple material items."""
        client.force_login(self.user)

        data = {
            # Header
            "supplier": "Global Materials Co",
            "invoice_number": "INV-2024-001",
            "date_received": "2024-04-07",
            # Formset management
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            # Item 1
            "form-0-name": "Cement Bags",
            "form-0-unit": "Bag",
            "form-0-quantity": "50",
            "form-0-rate": "12.50",
            "form-0-description": "Grade 42.5",
            # Item 2
            "form-1-name": "Steel Bars",
            "form-1-unit": "Ton",
            "form-1-quantity": "2",
            "form-1-rate": "850.00",
            "form-1-description": "12mm High Tensile",
        }

        response = client.post(self.url, data)
        # Should redirect to list view on success
        assert response.status_code == 302

        # Verify both items were created
        materials = MaterialEntity.objects.filter(project=self.project)
        assert materials.count() == 2

        item1 = materials.get(name="Cement Bags")
        assert item1.supplier == "Global Materials Co"
        assert item1.invoice_number == "INV-2024-001"
        assert item1.quantity == 50
        assert item1.rate == 12.50

        item2 = materials.get(name="Steel Bars")
        assert item2.supplier == "Global Materials Co"
        assert item2.invoice_number == "INV-2024-001"
        assert item2.quantity == 2
        assert item2.rate == 850.00

    def test_bulk_create_validation_error(self, client):
        """Test that validation errors are displayed correctly."""
        client.force_login(self.user)

        # Missing required header fields and invalid item data
        data = {
            # Header (Missing supplier)
            "supplier": "",
            "invoice_number": "INV-ERR",
            "date_received": "2024-04-07",
            # Formset management
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            # Item 1 (Missing name)
            "form-0-name": "",
            "form-0-unit": "Bag",
            "form-0-quantity": "50",
            "form-0-rate": "12.50",
        }

        response = client.post(self.url, data)
        assert response.status_code == 200

        # Check for header error
        header_form = response.context["header_form"]
        assert "supplier" in header_form.errors

        # Check for formset error
        formset = response.context["formset"]
        assert "name" in formset.forms[0].errors
