"""Tests for Ledger list view filters."""

from django.test import TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Ledger.models import FinancialStatement
from app.Ledger.tests.factories import LedgerFactory
from app.Project.tests.factories import ClientFactory


class TestLedgerFilters(TestCase):
    """Test cases for ledger list view filtering."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create()
        self.company = ClientFactory.create(users=[self.user])
        self.client.force_login(self.user)
        self.url = reverse(
            "ledger:ledger-list",
            kwargs={"company_id": self.company.pk},
        )

        # Create test ledgers
        # Get or create financial statements
        self.balance_sheet_fs, _ = FinancialStatement.objects.get_or_create(
            name="Balance Sheet"
        )
        self.income_statement_fs, _ = FinancialStatement.objects.get_or_create(
            name="Income Statement"
        )

        self.bs_ledger1 = LedgerFactory(
            company=self.company,
            code="1000",
            name="Cash",
            financial_statement=self.balance_sheet_fs,
        )
        self.bs_ledger2 = LedgerFactory(
            company=self.company,
            code="2000",
            name="Accounts Payable",
            financial_statement=self.balance_sheet_fs,
        )
        self.is_ledger1 = LedgerFactory(
            company=self.company,
            code="4000",
            name="Sales Revenue",
            financial_statement=self.income_statement_fs,
        )
        self.is_ledger2 = LedgerFactory(
            company=self.company,
            code="6000",
            name="Office Expenses",
            financial_statement=self.income_statement_fs,
        )

        # Create ledgers for another company (should not appear)
        self.other_company = ClientFactory()
        self.other_ledger = LedgerFactory(
            company=self.other_company,
            code="9999",
            name="Other Ledger",
            financial_statement=self.balance_sheet_fs,
        )

    def test_no_filters_shows_all_ledgers(self):
        """Test that without filters, all company ledgers are shown."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        ledgers = response.context["ledgers"]
        self.assertEqual(ledgers.count(), 4)  # Only this company's ledgers

        # Check all ledgers are present
        ledger_codes = [ledger.code for ledger in ledgers]
        self.assertIn("1000", ledger_codes)
        self.assertIn("2000", ledger_codes)
        self.assertIn("4000", ledger_codes)
        self.assertIn("6000", ledger_codes)
        self.assertNotIn("9999", ledger_codes)  # Other company's ledger

    def test_filter_by_financial_statement_balance_sheet(self):
        """Test filtering by Balance Sheet financial statement."""
        response = self.client.get(
            f"{self.url}?financial_statement={self.balance_sheet_fs.pk}"
        )
        self.assertEqual(response.status_code, 200)

        ledgers = response.context["ledgers"]
        self.assertEqual(ledgers.count(), 2)

        ledger_codes = [ledger.code for ledger in ledgers]
        self.assertIn("1000", ledger_codes)
        self.assertIn("2000", ledger_codes)
        self.assertNotIn("4000", ledger_codes)
        self.assertNotIn("6000", ledger_codes)

    def test_filter_by_financial_statement_income_statement(self):
        """Test filtering by Income Statement financial statement."""
        response = self.client.get(
            f"{self.url}?financial_statement={self.income_statement_fs.pk}"
        )
        self.assertEqual(response.status_code, 200)

        ledgers = response.context["ledgers"]
        self.assertEqual(ledgers.count(), 2)

        ledger_codes = [ledger.code for ledger in ledgers]
        self.assertIn("4000", ledger_codes)
        self.assertIn("6000", ledger_codes)
        self.assertNotIn("1000", ledger_codes)
        self.assertNotIn("2000", ledger_codes)

    def test_filter_by_code_exact_match(self):
        """Test filtering by exact code match."""
        response = self.client.get(f"{self.url}?code=1000")
        self.assertEqual(response.status_code, 200)

        ledgers = response.context["ledgers"]
        self.assertEqual(ledgers.count(), 1)
        self.assertEqual(ledgers.first().code, "1000")

    def test_filter_by_code_partial_match(self):
        """Test filtering by partial code match."""
        response = self.client.get(f"{self.url}?code=10")
        self.assertEqual(response.status_code, 200)

        ledgers = response.context["ledgers"]
        self.assertEqual(ledgers.count(), 1)  # Only 1000 matches

        ledger_codes = [ledger.code for ledger in ledgers]
        self.assertIn("1000", ledger_codes)

    def test_filter_by_name_exact_match(self):
        """Test filtering by exact name match."""
        response = self.client.get(f"{self.url}?name=Cash")
        self.assertEqual(response.status_code, 200)

        ledgers = response.context["ledgers"]
        self.assertEqual(ledgers.count(), 1)
        self.assertEqual(ledgers.first().name, "Cash")

    def test_filter_by_name_partial_match(self):
        """Test filtering by partial name match."""
        response = self.client.get(f"{self.url}?name=Revenue")
        self.assertEqual(response.status_code, 200)

        ledgers = response.context["ledgers"]
        self.assertEqual(ledgers.count(), 1)
        self.assertEqual(ledgers.first().name, "Sales Revenue")

    def test_filter_by_name_case_insensitive(self):
        """Test that name filtering is case insensitive."""
        response = self.client.get(f"{self.url}?name=cash")
        self.assertEqual(response.status_code, 200)

        ledgers = response.context["ledgers"]
        self.assertEqual(ledgers.count(), 1)
        self.assertEqual(ledgers.first().name, "Cash")

    def test_combined_filters(self):
        """Test combining multiple filters."""
        response = self.client.get(
            f"{self.url}?financial_statement={self.balance_sheet_fs.pk}&code=1000"
        )
        self.assertEqual(response.status_code, 200)

        ledgers = response.context["ledgers"]
        self.assertEqual(ledgers.count(), 1)
        self.assertEqual(ledgers.first().code, "1000")
        self.assertEqual(
            ledgers.first().financial_statement,
            self.balance_sheet_fs,
        )

    def test_filter_with_no_results(self):
        """Test filtering with criteria that returns no results."""
        response = self.client.get(f"{self.url}?code=9999")
        self.assertEqual(response.status_code, 200)

        ledgers = response.context["ledgers"]
        self.assertEqual(ledgers.count(), 0)

    def test_filter_values_preserved_in_context(self):
        """Test that filter values are preserved in the context."""
        response = self.client.get(
            f"{self.url}?financial_statement={self.balance_sheet_fs.pk}&code=1000&name=Cash"
        )
        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertEqual(
            context["filter_financial_statement"], str(self.balance_sheet_fs.pk)
        )
        self.assertEqual(context["filter_code"], "1000")
        self.assertEqual(context["filter_name"], "Cash")

    def test_financial_statement_choices_in_context(self):
        """Test that financial statement choices are available in context."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        choices = response.context["financial_statement_choices"]
        self.assertGreaterEqual(
            len(choices), 5
        )  # At least All + Balance Sheet + Income Statement
        self.assertEqual(choices[0]["value"], "")
        self.assertEqual(choices[0]["label"], "All")

        # Find our specific financial statements in the choices
        bs_choice = next((c for c in choices if c["label"] == "Balance Sheet"), {})
        is_choice = next((c for c in choices if c["label"] == "Income Statement"), {})

        self.assertIsNotNone(bs_choice)
        self.assertIsNotNone(is_choice)
        self.assertEqual(bs_choice["value"], str(self.balance_sheet_fs.pk))
        self.assertEqual(is_choice["value"], str(self.income_statement_fs.pk))
