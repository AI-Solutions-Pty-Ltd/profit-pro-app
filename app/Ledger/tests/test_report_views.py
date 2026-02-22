"""Tests for Report views."""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Ledger.models import FinancialStatement, Transaction
from app.Ledger.tests.factories import (
    LedgerFactory,
    TransactionFactory,
    VatFactory,
)
from app.Project.tests.factories import ClientFactory


class TestIncomeStatementView(TestCase):
    """Test cases for IncomeStatementView."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create()
        self.company = ClientFactory.create(users=[self.user])

        # Get or create Income Statement financial statement
        self.income_statement_fs, _ = FinancialStatement.objects.get_or_create(
            name="Income Statement"
        )

        # Create revenue ledger (code starts with 4)
        self.revenue_ledger = LedgerFactory.create(
            company=self.company,
            code="4001",
            name="Sales Revenue",
            financial_statement=self.income_statement_fs,
        )

        # Create expense ledger (code starts with 5)
        self.expense_ledger = LedgerFactory.create(
            company=self.company,
            code="5001",
            name="Office Expenses",
            financial_statement=self.income_statement_fs,
        )

        self.vat_rate = VatFactory(rate=Decimal("15.00"))

        # Create transactions
        self.revenue_transaction = TransactionFactory.create(
            company=self.company,
            debit_ledger=self.expense_ledger,
            credit_ledger=self.revenue_ledger,
            date=date.today(),
            type=Transaction.TransactionType.CREDIT,
            amount_incl_vat=Decimal("1150.00"),
            vat_rate=self.vat_rate,
        )

        self.expense_transaction = TransactionFactory.create(
            company=self.company,
            debit_ledger=self.expense_ledger,
            credit_ledger=self.revenue_ledger,
            date=date.today(),
            type=Transaction.TransactionType.DEBIT,
            amount_incl_vat=Decimal("575.00"),
            vat_rate=self.vat_rate,
        )

        self.client.force_login(self.user)
        self.url = reverse(
            "ledger:income-statement",
            kwargs={"company_id": self.company.pk},
        )

    def test_view_accessible_with_permission(self):
        """Test view is accessible when user has company access."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_shows_income_statement_data(self):
        """Test view shows correct income statement calculations."""
        # Provide date range that includes the test transactions
        start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        response = self.client.get(
            f"{self.url}?start_date={start_date}&end_date={end_date}"
        )
        self.assertEqual(response.status_code, 200)

        # Check context data
        self.assertEqual(response.context["company"], self.company)
        self.assertEqual(
            response.context["total_sum"], Decimal("-575.00")
        )  # Net result

        # Check that income statement items are present
        self.assertEqual(len(response.context["income_statement_items"]), 2)

        # Check revenue item (should be negative since it's credit)
        revenue_item = next(
            item
            for item in response.context["income_statement_items"]
            if item["code"] == "4001"
        )
        self.assertEqual(revenue_item["name"], "Sales Revenue")
        self.assertEqual(
            revenue_item["amount"], Decimal("-1150.00")
        )  # Credit shows as negative

        # Check expense item
        expense_item = next(
            item
            for item in response.context["income_statement_items"]
            if item["code"] == "5001"
        )
        self.assertEqual(expense_item["name"], "Office Expenses")
        self.assertEqual(
            expense_item["amount"], Decimal("575.00")
        )  # Debit shows as positive

    def test_view_with_date_range_filter(self):
        """Test view respects date range filters."""
        # Create transaction outside default date range
        TransactionFactory(
            company=self.company,
            debit_ledger=self.expense_ledger,
            credit_ledger=self.revenue_ledger,
            date=date.today() - timedelta(days=60),
            type=Transaction.TransactionType.CREDIT,
            amount_incl_vat=Decimal("1000.00"),
        )

        # Test with specific date range
        start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = date.today().strftime("%Y-%m-%d")

        response = self.client.get(
            f"{self.url}?start_date={start_date}&end_date={end_date}"
        )
        self.assertEqual(response.status_code, 200)

        # Old transaction should not be included, so we should still have the same total
        self.assertEqual(response.context["total_sum"], Decimal("-575.00"))

    def test_view_denied_without_permission(self):
        """Test view is denied when user lacks company access."""
        other_user = AccountFactory.create()
        self.client.force_login(other_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_view_denied_for_anonymous_user(self):
        """Test view is denied for anonymous users."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirects to login
