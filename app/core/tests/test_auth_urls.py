import pytest
from django.urls import reverse

# mark the test as requiring a database
pytestmark = pytest.mark.django_db


class TestUrls:
    def test_login(self, client):
        response = client.get(reverse("login"))
        assert response.status_code == 200

    def test_logout(self, client):
        response = client.post(reverse("logout"))
        assert response.status_code == 302

    def test_password_change(self, auth_client):
        response = auth_client.get(reverse("password_change"))
        assert response.status_code == 200

        # Test with wrong old password - should return 200 with form errors
        response = auth_client.post(
            reverse("password_change"),
            {
                "old_password": "wrongpassword",
                "new_password1": "NewPassword123",
                "new_password2": "NewPassword123",
            },
        )
        assert response.status_code == 200
        assert response.context["form"].errors  # Form should have errors

        # Test with correct old password - should redirect to success page
        response = auth_client.post(
            reverse("password_change"),
            {
                "old_password": "password",
                "new_password1": "NewPassword123",
                "new_password2": "NewPassword123",
            },
        )
        assert response.status_code == 302
        assert response.url == "/password_change/done/"

    def test_password_change_done(self, auth_client):
        response = auth_client.get(reverse("password_change_done"))
        assert response.status_code == 200

    def test_password_reset(self, client):
        response = client.get(reverse("password_reset"))
        assert response.status_code == 200

        response = client.post(reverse("password_reset"), {"email": "admin@admin.com"})
        assert response.status_code == 302

    def test_password_reset_done(self, client):
        response = client.get(reverse("password_reset_done"))
        assert response.status_code == 200

    def test_password_reset_confirm(self, client):
        response = client.get(
            reverse("password_reset_confirm", args=["uidb64", "token"])
        )
        assert response.status_code == 200

    def test_password_reset_complete(self, client):
        response = client.get(reverse("password_reset_complete"))
        assert response.status_code == 200
