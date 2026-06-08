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

    def test_favicon(self, client):
        response = client.get("/favicon.ico")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/x-icon"

    def test_404_handler(self, client):
        response = client.get("/this-path-does-not-exist/")
        assert response.status_code == 404
        assert "Page Not Found" in response.content.decode()


