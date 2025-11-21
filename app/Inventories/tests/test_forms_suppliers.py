from django.test import TestCase

from app.Inventories.forms_suppliers import SupplierCreateForm
from app.Inventories.models_suppliers import Supplier


class SupplierCreateFormTestCase(TestCase):
    """Test cases for SupplierCreateForm"""

    def test_valid_supplier_form(self):
        """Test valid supplier creation form"""
        form_data = {
            "description": "Test Supplier Ltd",
            "company_registration": "1234567890",
            "vat": True,
            "vat_number": 9876543210,
            "primary_contact": 27123456789,
            "email": "test@supplier.com",
            "active": True,
            "address": "123 Test Street, Johannesburg",
        }

        form = SupplierCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_supplier_form_missing_required(self):
        """Test form validation with missing required fields"""
        form_data = {
            "description": "",  # Required field
            "company_registration": "",  # Required field
            "email": "",  # Required field
            "primary_contact": "",  # Required field
        }

        form = SupplierCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)
        self.assertIn("company_registration", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("primary_contact", form.errors)

    def test_supplier_form_email_validation(self):
        """Test email validation in form"""
        form_data = {
            "description": "Test Supplier",
            "company_registration": "12345",
            "primary_contact": 1234567890,
            "email": "invalid-email-format",
            "active": True,
        }

        form = SupplierCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_supplier_form_vat_optional(self):
        """Test VAT fields are optional"""
        form_data = {
            "description": "Test Supplier",
            "company_registration": "12345",
            "primary_contact": 1234567890,
            "email": "test@supplier.com",
            "vat": "",  # Optional
            "vat_number": "",  # Optional
            "active": True,
        }

        form = SupplierCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_supplier_form_save(self):
        """Test form saves correctly"""
        form_data = {
            "description": "New Supplier",
            "company_registration": "NEW123",
            "vat": True,
            "vat_number": 111222333,
            "primary_contact": 27111222333,
            "email": "new@supplier.com",
            "active": True,
            "address": "456 New Street, Cape Town",
        }

        form = SupplierCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

        supplier = form.save()
        self.assertEqual(supplier.description, "New Supplier")
        self.assertEqual(supplier.company_registration, "NEW123")
        self.assertEqual(supplier.email, "new@supplier.com")

    def test_supplier_form_update(self):
        """Test form updates existing supplier"""
        supplier = Supplier.objects.create(
            description="Original Supplier",
            company_registration="ORIG001",
            primary_contact=1234567890,
            email="original@supplier.com",
            active=True,
        )

        form_data = {
            "description": "Updated Supplier",
            "company_registration": "UPD001",
            "primary_contact": 9876543210,
            "email": "updated@supplier.com",
            "active": False,
        }

        form = SupplierCreateForm(data=form_data, instance=supplier)
        self.assertTrue(form.is_valid())

        updated_supplier = form.save()
        self.assertEqual(updated_supplier.description, "Updated Supplier")
        self.assertEqual(updated_supplier.company_registration, "UPD001")
        self.assertEqual(updated_supplier.email, "updated@supplier.com")
