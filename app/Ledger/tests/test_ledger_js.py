"""Tests for Ledger list JavaScript functionality."""

from django.test import TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Ledger.tests.factories import LedgerFactory
from app.Project.tests.factories import ClientFactory


class TestLedgerJavaScript(TestCase):
    """Test cases for ledger list JavaScript functionality."""

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
        )
        LedgerFactory(
            company=self.company,
            code="4000",
            name="Sales Revenue",
        )

    def test_javascript_present_in_template(self):
        """Test that JavaScript is included in the template."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Check that the script content is present (rendered)
        self.assertContains(response, "document.addEventListener('DOMContentLoaded'")
        self.assertContains(response, "debounce")
        self.assertContains(response, "submitForm")
        self.assertContains(response, "filterForm")

    def test_filter_form_present(self):
        """Test that the filter form structure is correct."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Check form elements
        self.assertContains(response, 'form method="get"')
        self.assertContains(response, 'id="financial_statement"')

    def test_keyboard_shortcuts_tooltips(self):
        """Test that the input fields exist for keyboard shortcuts."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Check that the input fields exist (JavaScript will add tooltips)
        self.assertContains(response, 'id="code"')
        self.assertContains(response, 'id="name"')

    def test_filter_with_parameters_preserves_values(self):
        """Test that filter values are preserved when using GET parameters."""
        response = self.client.get(
            f"{self.url}?financial_statement=balance_sheet&code=1000&name=Cash"
        )
        self.assertEqual(response.status_code, 200)

        # Check that filter values are preserved in the form
        self.assertContains(response, 'value="balance_sheet"')
        self.assertContains(response, 'value="1000"')
        self.assertContains(response, 'value="Cash"')

    def test_empty_filter_state(self):
        """Test that the page loads correctly without any filters."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Should show all ledgers
        self.assertContains(response, "1000")
        self.assertContains(response, "4000")
        self.assertContains(response, "Cash")
        self.assertContains(response, "Sales Revenue")
