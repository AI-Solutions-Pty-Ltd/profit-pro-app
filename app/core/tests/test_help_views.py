"""Tests for Help Center view."""

from django.urls import reverse

from app.Account.tests.factories import AccountFactory


class TestHelpCenterView:
    """Test cases for the HelpCenterView."""

    def test_help_center_redirects_unauthenticated(self, client):
        """Verify that anonymous users are redirected to login."""
        url = reverse("help_center")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_help_center_authenticated_loads(self, client):
        """Verify that an authenticated user can load the help page."""
        user = AccountFactory(email="testuser@example.com")
        client.force_login(user)
        url = reverse("help_center")
        response = client.get(url)
        assert response.status_code == 200
        assert "help_modules" in response.context

    def test_help_center_evaluates_access_demo(self, client):
        """Verify that a user on DEMO_TIER sees active/demo statuses."""
        user = AccountFactory(email="demouser@example.com", subscription="DEMO_TIER")
        client.force_login(user)
        url = reverse("help_center")
        response = client.get(url)
        assert response.status_code == 200

        # Check context modules
        modules = response.context["help_modules"]
        business_mod = next(m for m in modules if m["id"] == "business_dashboard")
        assert business_mod["status"] == "Demo Available"
        assert business_mod["has_access"] is True
