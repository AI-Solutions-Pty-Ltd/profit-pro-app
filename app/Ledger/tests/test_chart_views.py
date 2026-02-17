"""Tests for Chart of Accounts views."""

from django.test import TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Ledger.models import Ledger
from app.Ledger.tests.factories import LedgerFactory
from app.Ledger.utils import (
    create_standard_chart_of_accounts,
    get_standard_chart_of_accounts,
)
from app.Project.tests.factories import ClientFactory


class TestStandardChartOfAccounts(TestCase):
    """Test cases for standard chart of accounts functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create()
        self.company = ClientFactory.create(users=[self.user])
        self.client.force_login(self.user)
        self.url = reverse(
            "ledger:create-standard-chart",
            kwargs={"company_id": self.company.pk},
        )

    def test_get_standard_chart_of_accounts(self):
        """Test getting the standard chart of accounts."""
        chart = get_standard_chart_of_accounts()

        # Should have 43 standard accounts
        self.assertEqual(len(chart), 43)

        # Check structure of returned data
        for account in chart:
            self.assertIn("code", account)
            self.assertIn("name", account)
            self.assertIn("financial_statement", account)
            self.assertEqual(len(account["code"]), 4)  # 4-digit codes

    def test_create_standard_chart_of_accounts(self):
        """Test creating standard chart of accounts for a company."""
        # Initially no ledgers
        self.assertEqual(Ledger.objects.filter(company=self.company).count(), 0)

        # Create standard chart
        ledgers = create_standard_chart_of_accounts(self.company)

        # Should have created 43 ledgers
        self.assertEqual(len(ledgers), 43)
        self.assertEqual(Ledger.objects.filter(company=self.company).count(), 43)

        # Check specific ledgers were created
        cash_ledger = Ledger.objects.get(company=self.company, code="1000")
        self.assertEqual(cash_ledger.name, "Cash and Cash Equivalents")
        self.assertEqual(
            cash_ledger.financial_statement, Ledger.FinancialStatement.BALANCE_SHEET
        )

        sales_ledger = Ledger.objects.get(company=self.company, code="4000")
        self.assertEqual(sales_ledger.name, "Sales Revenue")
        self.assertEqual(
            sales_ledger.financial_statement, Ledger.FinancialStatement.INCOME_STATEMENT
        )

    def test_create_standard_chart_view_post(self):
        """Test POST request to create standard chart."""
        # Initially no ledgers
        self.assertEqual(Ledger.objects.filter(company=self.company).count(), 0)

        response = self.client.post(self.url, follow=True)

        # Debug: check messages
        messages = list(response.context.get("messages", []))
        for msg in messages:
            print(f"Message: {msg}")

        # Should be on ledger list page
        self.assertContains(response, "Ledgers")

        # Should have created 43 ledgers
        self.assertEqual(Ledger.objects.filter(company=self.company).count(), 43)

    def test_create_standard_chart_view_with_existing_ledgers(self):
        """Test that standard chart is not created if ledgers already exist."""
        # Create one ledger first
        LedgerFactory(company=self.company, code="9999", name="Test Ledger")

        initial_count = Ledger.objects.filter(company=self.company).count()

        response = self.client.post(self.url)

        # Should redirect to ledger list
        self.assertRedirects(
            response,
            reverse("ledger:ledger-list", kwargs={"company_id": self.company.pk}),
        )

        # Count should be unchanged
        self.assertEqual(
            Ledger.objects.filter(company=self.company).count(), initial_count
        )

    def test_view_denied_without_permission(self):
        """Test view is denied when user lacks company access."""
        other_user = AccountFactory.create()
        self.client.force_login(other_user)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_view_denied_for_anonymous_user(self):
        """Test view is denied for anonymous users."""
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)  # Redirects to login
