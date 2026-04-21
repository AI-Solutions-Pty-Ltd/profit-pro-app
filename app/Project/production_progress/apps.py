from django.apps import AppConfig


class ProductionProgressConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.Project.production_progress"
    verbose_name = "Production Progress"
