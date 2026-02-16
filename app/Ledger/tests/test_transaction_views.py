"""Tests for Transaction views."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.tests.factories import (
    BillFactory,
    StructureFactory,
)
from app.Ledger.models import Transaction
from app.Ledger.tests.factories import LedgerFactory, TransactionFactory, VatFactory
from app.Project.tests.factories import ClientFactory, ProjectFactory


class TestTransactionListView(TestCase):
    """Test cases for TransactionListView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory()
        self.company = ClientFactory(users=[self.user])
        self.ledger = LedgerFactory(company=self.company)
        self.transaction1 = TransactionFactory(
            ledger=self.ledger,
            date=timezone.now().date(),
            type=Transaction.TransactionType.DEBIT,
            amount_incl_vat=Decimal("100.00"),
        )
        self.transaction2 = TransactionFactory(
            ledger=self.ledger,
            date=timezone.now().date(),
            type=Transaction.TransactionType.CREDIT,
            amount_incl_vat=Decimal("200.00"),
        )
        self.client.force_login(self.user)  # type: ignore
        self.url = reverse(
            "ledger:transaction-list",
            kwargs={"company_id": self.company.pk},  # type: ignore
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible when user has company access."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_shows_company_transactions(self):
        """Test view shows transactions for the correct company."""
        other_company = ClientFactory()
        other_ledger = LedgerFactory(company=other_company)
        other_transaction = TransactionFactory(ledger=other_ledger)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        transactions = response.context["transactions"]
        self.assertIn(self.transaction1, transactions)
        self.assertIn(self.transaction2, transactions)
        self.assertNotIn(other_transaction, transactions)

    def test_view_denied_without_company_access(self):
        """Test view denies access when user doesn't have company access."""
        other_user = AccountFactory()
        self.client.force_login(other_user)  # type: ignore

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ledger/transaction_list.html")

    def test_context_data(self):
        """Test context data is correct."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["company"], self.company)
        self.assertIn("ledgers", response.context)


class TestTransactionDetailView(TestCase):
    """Test cases for TransactionDetailView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory()
        self.company = ClientFactory(users=[self.user])
        self.ledger = LedgerFactory(company=self.company)
        self.transaction = TransactionFactory(
            ledger=self.ledger,
            date=timezone.now().date(),
            type=Transaction.TransactionType.DEBIT,
            amount_incl_vat=Decimal("100.00"),
        )
        self.client.force_login(self.user)  # type: ignore
        self.url = reverse(
            "ledger:transaction-detail",
            kwargs={"company_id": self.company.pk, "pk": self.transaction.pk},  # type: ignore
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible when user has company access."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_shows_correct_transaction(self):
        """Test view shows the correct transaction."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["transaction"], self.transaction)

    def test_view_denied_without_company_access(self):
        """Test view denies access when user doesn't have company access."""
        other_user = AccountFactory()
        self.client.force_login(other_user)  # type: ignore

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_template_used(self):
        """Test correct template is used."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ledger/transaction_detail.html")


class TestTransactionCreateRoutingView(TestCase):
    """Test generic transaction create routing by VAT registration."""

    def setUp(self):
        self.user = AccountFactory()
        self.non_vat_company = ClientFactory(users=[self.user], vat_registered=False)
        self.vat_company = ClientFactory(users=[self.user], vat_registered=True)
        self.client.force_login(self.user)  # type: ignore

    def test_generic_create_redirects_to_non_vat_view(self):
        """Test non-VAT company routing."""
        response = self.client.get(
            reverse(
                "ledger:transaction-create",
                kwargs={"company_id": self.non_vat_company.pk},  # type: ignore
            )
        )
        self.assertRedirects(
            response,
            reverse(
                "ledger:transaction-create-non-vat",
                kwargs={"company_id": self.non_vat_company.pk},  # type: ignore
            ),
        )

    def test_generic_create_redirects_to_vat_view(self):
        """Test VAT company routing."""
        response = self.client.get(
            reverse(
                "ledger:transaction-create",
                kwargs={"company_id": self.vat_company.pk},  # type: ignore
            )
        )
        self.assertRedirects(
            response,
            reverse(
                "ledger:transaction-create-vat",
                kwargs={"company_id": self.vat_company.pk},  # type: ignore
            ),
        )


class BaseTransactionCreateScenarioTest(TestCase):
    """Shared setup for VAT/non-VAT transaction create tests."""

    vat_registered = False

    def setUp(self):
        self.user = AccountFactory()
        self.company = ClientFactory(
            users=[self.user], vat_registered=self.vat_registered
        )
        self.ledger = LedgerFactory(company=self.company)

        self.project = ProjectFactory(client=self.company)
        self.structure = StructureFactory(project=self.project, name="Main Structure")
        self.bill = BillFactory(structure=self.structure)

        self.other_company = ClientFactory(vat_registered=not self.vat_registered)
        self.other_project = ProjectFactory(client=self.other_company)
        self.other_structure = StructureFactory(
            project=self.other_project,
            name="Other Structure",
        )
        self.other_bill = BillFactory(structure=self.other_structure)

        self.client.force_login(self.user)  # type: ignore


class TestNonVatTransactionCreateView(BaseTransactionCreateScenarioTest):
    """Test non-VAT transaction creation behavior."""

    vat_registered = False

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "ledger:transaction-create-non-vat",
            kwargs={"company_id": self.company.pk},  # type: ignore
        )

    def test_view_accessible_with_permission(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_form_submission_sets_non_vat_defaults(self):
        """Test non-VAT create form stores VAT defaults and total."""
        data = {
            "ledger": self.ledger.pk,  # type: ignore
            "date": timezone.now().date(),
            "type": Transaction.TransactionType.DEBIT,
            "total": "100.00",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        transaction = Transaction.objects.get(ledger=self.ledger)
        self.assertEqual(transaction.amount_excl_vat, Decimal("100.00"))
        self.assertEqual(transaction.amount_incl_vat, Decimal("100.00"))
        self.assertFalse(transaction.vat)
        self.assertIsNone(transaction.vat_rate)

    def test_template_has_total_field_not_vat_rate(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Total")
        self.assertNotContains(response, "VAT Rate")
        self.assertContains(response, 'id="structure_filter"')
        self.assertContains(response, 'id="bill_search"')

    def test_wrong_vat_view_redirects_to_non_vat_view(self):
        """Test guard redirect for non-VAT companies on VAT path."""
        vat_url = reverse(
            "ledger:transaction-create-vat",
            kwargs={"company_id": self.company.pk},  # type: ignore
        )
        response = self.client.get(vat_url)
        self.assertRedirects(response, self.url)


class TestVatTransactionCreateView(BaseTransactionCreateScenarioTest):
    """Test VAT transaction creation behavior."""

    vat_registered = True

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "ledger:transaction-create-vat",
            kwargs={"company_id": self.company.pk},  # type: ignore
        )
        today = timezone.now().date()
        self.current_vat = VatFactory.create(
            name="Current VAT",
            rate=Decimal("15.00"),
            start_date=today - timedelta(days=5),
            end_date=today + timedelta(days=5),
        )
        self.expired_vat = VatFactory.create(
            name="Expired VAT",
            rate=Decimal("14.00"),
            start_date=today - timedelta(days=100),
            end_date=today - timedelta(days=50),
        )
        self.no_vat = VatFactory.create(
            name="No VAT",
            rate=Decimal("0.00"),
            start_date=None,
            end_date=None,
        )

    def test_view_accessible_with_permission(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_form_submission_with_vat_inclusive_calculates_values(self):
        """Test VAT inclusive amount creates matching inclusive/exclusive fields."""
        data = {
            "ledger": self.ledger.pk,  # type: ignore
            "date": timezone.now().date(),
            "type": Transaction.TransactionType.DEBIT,
            "vat_rate": self.current_vat.pk,
            "amount": "115.00",
            "vat_mode": "inclusive",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        transaction = Transaction.objects.get(ledger=self.ledger)
        self.assertTrue(transaction.vat)
        self.assertEqual(transaction.vat_rate, self.current_vat)
        self.assertEqual(transaction.amount_incl_vat, Decimal("115.00"))
        self.assertEqual(transaction.amount_excl_vat, Decimal("100.00"))

    def test_form_rejects_vat_rate_outside_selected_date(self):
        """Test backend validator blocks VAT rate not active for transaction date."""
        data = {
            "ledger": self.ledger.pk,  # type: ignore
            "date": timezone.now().date(),
            "type": Transaction.TransactionType.DEBIT,
            "vat_rate": self.expired_vat.pk,
            "amount": "100.00",
            "vat_mode": "exclusive",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Selected VAT rate is not active for the chosen date."
        )

    def test_template_disables_vat_rate_until_date_selected(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'id="id_vat_rate"')
        self.assertContains(response, "disabled")

    def test_form_submission_with_no_vat_sets_vat_false(self):
        """Test 'No VAT' option sets vat=False and uses amount for both fields."""
        data = {
            "ledger": self.ledger.pk,  # type: ignore
            "date": timezone.now().date(),
            "type": Transaction.TransactionType.DEBIT,
            "vat_rate": self.no_vat.pk,
            "amount": "100.00",
            "vat_mode": "inclusive",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        transaction = Transaction.objects.get(ledger=self.ledger)
        self.assertFalse(transaction.vat)
        self.assertEqual(transaction.vat_rate, self.no_vat)
        self.assertEqual(transaction.amount_incl_vat, Decimal("100.00"))
        self.assertEqual(transaction.amount_excl_vat, Decimal("100.00"))

    def test_wrong_non_vat_view_redirects_to_vat_view(self):
        """Test guard redirect for VAT companies on non-VAT path."""
        non_vat_url = reverse(
            "ledger:transaction-create-non-vat",
            kwargs={"company_id": self.company.pk},  # type: ignore
        )
        response = self.client.get(non_vat_url)
        self.assertRedirects(response, self.url)
