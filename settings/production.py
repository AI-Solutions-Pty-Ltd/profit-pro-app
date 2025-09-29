from .base import *  # noqa
import os

print("Production settings loaded")

ALLOWED_HOSTS: list[str] = os.getenv("ALLOWED_HOSTS", "").split(",")

DB = os.getenv("DB")
DB_HOST = os.getenv("DB_HOST")
DB_USER_PWD = os.getenv("DB_USER_PWD")
DB_USER = os.getenv("DB_USER")

if not all([DB, DB_HOST, DB_USER_PWD, DB_USER]):
    raise ValueError("DB, DB_HOST, DB_USER_PWD, DB_USER are not set")

DEBUG = False

SECRET_KEY = os.getenv("SECRET_KEY", None)

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": DB,
        "USER": DB_USER,
        "PASSWORD": DB_USER_PWD,
        "HOST": DB_HOST,
    }
}
