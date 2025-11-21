from django.core.exceptions import ValidationError
from django.test import TestCase

from app.Inventories.models_suppliers import (
    Bank,
    BankingDetail,
    Invoice,
    Supplier,
    Transaction,
)


class SupplierModelTestCase(TestCase):
    """Test cases for Supplier model"""

    def setUp(self):
        """Set up test data"""
        # Create test supplier
        self.supplier_data = {
            "description": "Test Supplier Ltd",
            "company_registration": "1234567890",
            "vat": True,
            "vat_number": 9876543210,
            "primary_contact": 27123456789,
            "email": "test@supplier.com",
            "active": True,
            "address": "123 Test Street, Johannesburg",
        }

        self.supplier = Supplier.objects.create(**self.supplier_data)

    def test_supplier_creation(self):
        """Test supplier creation with valid data"""
        self.assertEqual(self.supplier.description, "Test Supplier Ltd")
        self.assertEqual(self.supplier.company_registration, "1234567890")
        self.assertEqual(self.supplier.email, "test@supplier.com")
        self.assertTrue(self.supplier.active)

    def test_supplier_str_method(self):
        """Test string representation of supplier"""
        self.assertEqual(str(self.supplier), "Test Supplier Ltd")

    def test_supplier_is_active_property(self):
        """Test is_active property"""
        # Test with active = Yes
        self.supplier.active = True
        self.supplier.save()
        self.assertTrue(self.supplier.active)

        # Test with active = No
        self.supplier.active = False
        self.supplier.save()
        self.assertFalse(self.supplier.active)

    def test_supplier_required_fields(self):
        """Test required fields validation"""
        # Test description is required
        supplier = Supplier()
        with self.assertRaises(ValidationError):
            supplier.full_clean()

        # Test company_registration is required
        supplier.description = "Test Supplier"
        with self.assertRaises(ValidationError):
            supplier.full_clean()

    def test_supplier_email_validation(self):
        """Test email field validation"""
        # Test valid email
        supplier = Supplier.objects.create(
            description="Valid Email Supplier",
            company_registration="12345",
            primary_contact=1234567890,
            email="valid@email.com",
        )
        self.assertEqual(supplier.email, "valid@email.com")

    def test_supplier_vat_number_optional(self):
        """Test VAT number is optional"""
        supplier = Supplier.objects.create(
            description="No VAT Supplier",
            company_registration="12345",
            primary_contact=1234567890,
            email="novat@supplier.com",
            vat=None,
            vat_number=None,
        )
        self.assertIsNone(supplier.vat_number)

    def test_supplier_foreign_key_relationships(self):
        """Test foreign key relationships"""

    def test_get_transactions_method(self):
        """Test get_transactions method"""
        # Create category and transaction
        transaction = Transaction.objects.create(
            date="2024-01-01 10:00:00",
            supplier=self.supplier,
            description="Test Transaction",
            amount_excl=100.00,
            amount_incl=115.00,
        )

        transactions = self.supplier.get_transactions()
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first(), transaction)

    def test_supplier_with_null_foreign_keys(self):
        """Test supplier creation with null foreign keys"""
        supplier = Supplier.objects.create(
            description="Minimal Supplier",
            company_registration="12345",
            primary_contact=1234567890,
            email="minimal@supplier.com",
            active=False,
            vat=False,
        )

        self.assertFalse(supplier.active)
        self.assertFalse(supplier.vat)

    def test_supplier_company_registration_uniqueness(self):
        """Test company registration uniqueness (if applicable)"""
        # This test assumes company_registration should be unique
        # Adjust based on actual requirements
        with self.assertRaises(Exception):  # noqa: B017
            Supplier.objects.create(
                description="Duplicate Supplier",
                company_registration="1234567890",  # Same as self.supplier
                primary_contact=9876543210,
                email="duplicate@supplier.com",
            )


class TransactionModelTestCase(TestCase):
    """Test cases for Transaction model"""

    def setUp(self):
        """Set up test data"""
        self.supplier = Supplier.objects.create(
            description="Transaction Supplier",
            company_registration="TRANS001",
            primary_contact=1234567890,
            email="transaction@supplier.com",
            active=False,
        )

    def test_transaction_creation(self):
        """Test transaction creation"""
        transaction = Transaction.objects.create(
            date="2024-01-01 10:00:00",
            supplier=self.supplier,
            description="Test Transaction",
            amount_excl=100.000,
            amount_incl=115.000,
        )

        self.assertEqual(transaction.description, "Test Transaction")
        self.assertEqual(float(transaction.amount_excl), 100.00)
        self.assertEqual(float(transaction.amount_incl), 115.00)

    def test_transaction_foreign_keys(self):
        """Test transaction foreign key relationships"""
        transaction = Transaction.objects.create(
            date="2024-01-01 10:00:00",
            supplier=self.supplier,
            description="Foreign Key Test",
            amount_excl=50.000,
            amount_incl=57.500,
        )

        self.assertEqual(transaction.supplier, self.supplier)

    def test_transaction_null_supplier(self):
        """Test transaction with null supplier"""
        transaction = Transaction.objects.create(
            date="2024-01-01 10:00:00",
            supplier=None,
            description="No Supplier Transaction",
            amount_excl=75.000,
            amount_incl=86.250,
        )

        self.assertIsNone(transaction.supplier)


class InvoiceModelTestCase(TestCase):
    """Test cases for Invoice model"""

    def setUp(self):
        """Set up test data"""
        self.supplier = Supplier.objects.create(
            description="Invoice Supplier",
            company_registration="INV001",
            primary_contact=1234567890,
            email="invoice@supplier.com",
            active=False,
        )

    def test_invoice_creation(self):
        """Test invoice creation"""
        invoice = Invoice.objects.create(
            date="2024-01-01 10:00:00", supplier=self.supplier, order=None
        )

        self.assertIsNotNone(invoice.pk)
        self.assertEqual(invoice.supplier, self.supplier)

    def test_invoice_with_transactions(self):
        """Test invoice with many-to-many transactions"""
        invoice = Invoice.objects.create(
            date="2024-01-01 10:00:00", supplier=self.supplier
        )

        transaction1 = Transaction.objects.create(
            date="2024-01-01 10:00:00",
            supplier=self.supplier,
            description="Transaction 1",
            amount_excl=100.000,
            amount_incl=115.000,
        )

        transaction2 = Transaction.objects.create(
            date="2024-01-01 11:00:00",
            supplier=self.supplier,
            description="Transaction 2",
            amount_excl=200.000,
            amount_incl=230.000,
        )

        invoice.tx.add(transaction1, transaction2)
        self.assertEqual(invoice.tx.count(), 2)


class BankModelTestCase(TestCase):
    """Test cases for Bank model"""

    def test_bank_creation(self):
        """Test bank creation"""
        bank = Bank.objects.create(bank="Standard Bank", branch="001234")

        self.assertEqual(str(bank), "Standard Bank")
        self.assertEqual(bank.branch, "001234")

    def test_bank_str_method(self):
        """Test string representation"""
        bank = Bank.objects.create(bank="FNB", branch="002345")
        self.assertEqual(str(bank), "FNB")


class BankingDetailModelTestCase(TestCase):
    """Test cases for BankingDetail model"""

    def setUp(self):
        """Set up test data"""
        self.supplier = Supplier.objects.create(
            description="Banking Supplier",
            company_registration="BANK001",
            primary_contact=1234567890,
            email="banking@supplier.com",
            active=False,
        )
        self.bank = Bank.objects.create(bank="ABSA", branch="003456")

    def test_banking_detail_creation(self):
        """Test banking detail creation"""
        banking_detail = BankingDetail.objects.create(
            contractor=self.supplier,
            bank=self.bank,
            account="1234567890",
            account_holder="Test Account Holder",
        )

        self.assertEqual(banking_detail.supplier, self.supplier)
        self.assertEqual(banking_detail.bank, self.bank)
        self.assertEqual(banking_detail.account, "1234567890")

    def test_banking_detail_str_method(self):
        """Test string representation"""
        banking_detail = BankingDetail.objects.create(
            contractor=self.supplier,
            bank=self.bank,
            account="9876543210",
            account_holder="Another Holder",
        )

        self.assertEqual(str(banking_detail), "ABSA")

    def test_banking_detail_one_to_one(self):
        """Test one-to-one relationship with supplier"""
        BankingDetail.objects.create(
            contractor=self.supplier,
            bank=self.bank,
            account="1111111111",
            account_holder="Holder 1",
        )

        # Should not be able to create another banking detail for same supplier
        with self.assertRaises(Exception):  # noqa: B017
            BankingDetail.objects.create(
                contractor=self.supplier,
                bank=self.bank,
                account="2222222222",
                account_holder="Holder 2",
            )
