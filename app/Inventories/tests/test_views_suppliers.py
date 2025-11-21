from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from app.Inventories.models_suppliers import (
    Bank,
    BankingDetail,
    Invoice,
    Supplier,
    Transaction,
)


class SupplierViewsTestCase(TestCase):
    """Test cases for supplier views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create test user with proper permissions
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Create groups and add user
        self.material_manager_group = Group.objects.create(name="Material Manager")
        self.super_group = Group.objects.create(name="super")
        self.user.groups.add(self.material_manager_group)

        # Create test supplier
        self.supplier = Supplier.objects.create(
            description="Test Supplier Ltd",
            company_registration="1234567890",
            vat=True,
            vat_number=9876543210,
            primary_contact=27123456789,
            email="test@supplier.com",
            active=True,
            address="123 Test Street, Johannesburg",
        )

        # Create category and transaction
        self.transaction = Transaction.objects.create(
            date="2024-01-01 10:00:00",
            supplier=self.supplier,
            category=Transaction.Category.INVOICE,
            description="Test Transaction",
            amount_excl=100.000,
            amount_incl=115.000,
        )

        # Create invoice
        self.invoice = Invoice.objects.create(
            date="2024-01-01 10:00:00", supplier=self.supplier
        )
        self.invoice.tx.add(self.transaction)

    def test_supplier_list_view_authenticated(self):
        """Test supplier list view with authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("suppliers:supplier_list_view"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Supplier Ltd")
        self.assertTemplateUsed(response, "Suppliers/supplier_list.html")

    def test_supplier_list_view_unauthenticated(self):
        """Test supplier list view redirects unauthenticated user"""
        response = self.client.get(reverse("suppliers:supplier_list_view"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_supplier_detail_view(self):
        """Test supplier detail view"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse(
            "suppliers:supplier_detail_view", kwargs={"supplier": self.supplier.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Supplier Ltd")
        self.assertTemplateUsed(response, "Suppliers/supplier_detail.html")

    def test_supplier_create_view_get(self):
        """Test supplier create view GET request"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("suppliers:supplier_create_view"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Suppliers/supplier_create.html")

    def test_supplier_create_view_post(self):
        """Test supplier create view POST request"""
        self.client.login(username="testuser", password="testpass123")

        data = {
            "description": "New Test Supplier",
            "company_registration": "NEW123456",
            "vat": True,
            "vat_number": 111222333,
            "primary_contact": 27111222333,
            "email": "newtest@supplier.com",
            "active": True,
            "address": "789 New Street, Johannesburg",
        }

        response = self.client.post(reverse("suppliers:supplier_create_view"), data)

        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(
            Supplier.objects.filter(description="New Test Supplier").exists()
        )

    def test_supplier_statement_view(self):
        """Test supplier statement view"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse(
            "suppliers:supplier_statement_view", kwargs={"supplier": self.supplier.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Supplier Ltd")
        self.assertContains(response, "Test Transaction")
        self.assertTemplateUsed(response, "Suppliers/supplier_statement.html")

    def test_supplier_update_post(self):
        """Test supplier update via detail view"""
        self.client.login(username="testuser", password="testpass123")

        data = {
            "description": "Updated Supplier Name",
            "company_registration": "UPD123456",
            "primary_contact": 27999999999,
            "email": "updated@supplier.com",
            "active": True,
            "update": "Update",  # This is the submit button name
        }

        url = reverse(
            "suppliers:supplier_detail_view", kwargs={"supplier": self.supplier.id}
        )
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)  # Redirect after update

        updated_supplier = Supplier.objects.get(id=self.supplier.id)
        self.assertEqual(updated_supplier.description, "Updated Supplier Name")
        self.assertEqual(updated_supplier.email, "updated@supplier.com")

    def test_supplier_search_in_list(self):
        """Test supplier search functionality in list view"""
        self.client.login(username="testuser", password="testpass123")

        # Create additional suppliers
        Supplier.objects.create(
            description="Another Supplier",
            company_registration="ANOTHER001",
            primary_contact=1234567890,
            email="another@supplier.com",
            active=True,
        )

        response = self.client.get(reverse("suppliers:supplier_list_view"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Supplier Ltd")
        self.assertContains(response, "Another Supplier")

    def test_supplier_with_no_transactions(self):
        """Test supplier with no transactions"""
        new_supplier = Supplier.objects.create(
            description="No Transaction Supplier",
            company_registration="NOTX001",
            primary_contact=1234567890,
            email="notx@supplier.com",
            active=True,
        )

        self.client.login(username="testuser", password="testpass123")
        url = reverse(
            "suppliers:supplier_statement_view", kwargs={"supplier": new_supplier.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Transaction Supplier")

    def test_supplier_permissions(self):
        """Test supplier views respect permissions"""
        # Create user without proper permissions
        User.objects.create_user(username="regularuser", password="regularpass123")

        self.client.login(username="regularuser", password="regularpass123")
        response = self.client.get(reverse("suppliers:supplier_list_view"))

        # Should be denied access (redirect or 403)
        self.assertEqual(response.status_code, 302)

    def test_supplier_with_bank_details(self):
        """Test supplier with banking details"""
        bank = Bank.objects.create(bank="Test Bank", branch="123456")
        BankingDetail.objects.create(
            contractor=self.supplier,
            bank=bank,
            account="1234567890",
            account_holder="Test Holder",
        )

        self.client.login(username="testuser", password="testpass123")
        url = reverse(
            "suppliers:supplier_detail_view", kwargs={"supplier": self.supplier.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_supplier_invoice_file_handling(self):
        """Test supplier invoice file upload/download"""
        # This would require actual file upload testing with test files
        # For now, test the URL patterns and basic functionality
        self.client.login(username="testuser", password="testpass123")

        # Test invoice file serve view
        url = reverse(
            "suppliers:supplier_invoice_file_serve_view",
            kwargs={"invoice": self.invoice.pk},
        )
        response = self.client.get(url)

        # Should handle missing file gracefully
        self.assertEqual(response.status_code, 302)  # Redirect with error message
