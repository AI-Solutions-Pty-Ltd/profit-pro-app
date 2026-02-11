from django.urls import reverse


class TestUrls:
    def test_home(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 200

    def test_about(self, client):
        response = client.get(reverse("about"))
        assert response.status_code == 200

    def test_features(self, client):
        response = client.get(reverse("features"))
        assert response.status_code == 200

    def test_register(self, client):
        response = client.get(reverse("users:auth:register"))
        assert response.status_code == 200

        # test register
        response = client.post(
            reverse("users:auth:register"),
            {
                "email": "test@test.com",
                "first_name": "test",
                "last_name": "test",
                "password1": "NewPassword123",
                "password2": "NewPassword123",
            },
        )
        assert response.status_code == 302
