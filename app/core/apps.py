import importlib

from django.apps import AppConfig
from django.conf import settings


class CoreConfig(AppConfig):
    name = "app.core"

    def ready(self):
        """
        Trigger autodiscovery of quick_create modules across all apps.
        """
        self.autodiscover_quick_create()

    def autodiscover_quick_create(self):
        """
        Iterates through project apps and attempts to import 'quick_create' modules.
        This triggers registration of resources with the central QuickCreateRegistry.
        """
        for app in settings.INSTALLED_APPS:
            # We only care about our local apps (usually starting with app.)
            if not app.startswith("app."):
                continue

            try:
                module_path = f"{app}.quick_create"
                importlib.import_module(module_path)
            except ImportError:
                # If the app doesn't have a quick_create.py, just skip it
                pass
