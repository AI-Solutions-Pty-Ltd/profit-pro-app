from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.Account"

    def ready(self):
        """Import signals when the app is ready."""
        import app.Account.signals  # noqa: F401
