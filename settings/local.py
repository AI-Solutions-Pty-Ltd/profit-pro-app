from .base import *  # noqa
from .base import BASE_DIR
import os

print("Local settings loaded")

DEBUG = True
SECRET_KEY = "django-insecure-l^sjb(j9w-3fe0+!qiu!j7c&bu!vrv=m@#1e6zwuwfqbm35v!i"
ALLOWED_HOSTS: list[str] = ["*"]

DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB = os.getenv("DB")

if DB_TYPE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / DB,
        }
    }
else:
    DB_HOST = os.getenv("DB_HOST")
    DB_USER_PWD = os.getenv("DB_USER_PWD")
    DB_USER = os.getenv("DB_USER")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": DB,
            "USER": DB_USER,
            "PASSWORD": DB_USER_PWD,
            "HOST": DB_HOST,
        }
    }

INSTALLED_APPS += ["django_browser_reload"]  # noqa: F405

MIDDLEWARE += [  # noqa: F405
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]
