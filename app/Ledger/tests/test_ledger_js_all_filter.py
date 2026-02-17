"""Tests for "All" filter functionality in JavaScript."""

from django.test import TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Ledger.tests.factories import LedgerFactory
from app.Project.tests.factories import ClientFactory


class TestLedgerAllFilter(TestCase):
    """Test cases for 'All' filter functionality."""

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
        LedgerFactory(
            company=self.company,
            code="1000",
            name="Cash",
            financial_statement="balance_sheet",
        )
        LedgerFactory(
            company=self.company,
            code="4000",
            name="Sales Revenue",
            financial_statement="income_statement",
        )

    def test_filter_with_all_shows_all_ledgers(self):
        """Test that selecting 'All' shows all ledgers."""
        # Request with empty financial_statement (equivalent to "All")
        response = self.client.get(f"{self.url}?financial_statement=")
        self.assertEqual(response.status_code, 200)

        # Should show both ledgers
        self.assertContains(response, "1000")
        self.assertContains(response, "4000")
        self.assertContains(response, "Cash")
        self.assertContains(response, "Sales Revenue")

    def test_clear_all_filters_with_empty_params(self):
        """Test clearing all filters with empty parameters."""
        # Start with filters applied
        response = self.client.get(
            f"{self.url}?financial_statement=balance_sheet&code=1000"
        )
        self.assertEqual(response.status_code, 200)

        # Should only show balance sheet ledgers
        self.assertContains(response, "1000")
        self.assertNotContains(response, "4000")

        # Clear all filters
        response = self.client.get(f"{self.url}?financial_statement=&code=&name=")
        self.assertEqual(response.status_code, 200)

        # Should show all ledgers again
        self.assertContains(response, "1000")
        self.assertContains(response, "4000")

    def test_javascript_handles_empty_financial_statement(self):
        """Test that JavaScript can handle empty financial statement value."""
        response = self.client.get(f"{self.url}?financial_statement=")
        self.assertEqual(response.status_code, 200)

        # The form should render correctly with empty value
        self.assertContains(response, 'value=""')

        # JavaScript should be present to handle the change
        self.assertContains(
            response, "financialStatementSelect.addEventListener('change'"
        )
