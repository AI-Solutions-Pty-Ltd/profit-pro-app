from datetime import datetime

from django.apps import AppConfig
from django.shortcuts import get_object_or_404


class InventoriesConfig(AppConfig):
    name = "app.Inventories"


class ObjectMixin:
    def get_object(self, model):
        obj = None
        if self is not None:
            obj = get_object_or_404(model, id=self)
        return obj

    @staticmethod
    def get_default_context(title: str):
        context = {
            "title": title,
            "year": datetime.now().year,
            "date": datetime.now(),
        }
        return context
