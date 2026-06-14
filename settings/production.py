import os

from .base import *  # noqa

print("Production settings loaded")

ALLOWED_HOSTS: list[str] = os.getenv("ALLOWED_HOSTS", "").split(",")

DB = os.getenv("DB")
DB_HOST = os.getenv("DB_HOST")
DB_USER_PWD = os.getenv("DB_USER_PWD")
DB_USER = os.getenv("DB_USER")

if not all([DB, DB_HOST, DB_USER_PWD, DB_USER]):
    raise ValueError("DB, DB_HOST, DB_USER_PWD, DB_USER are not set")

# Fix: ADMINS must be a list of (name, email) tuples
_admin_email = os.getenv("ADMIN_EMAIL", "")
ADMINS = [("Admin", _admin_email)] if _admin_email else []

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

# Ensure logs directory exists before logging is configured
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)  # noqa: F405

# Write Django errors to a log file readable via cPanel File Manager
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "error_file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django_errors.log"),  # noqa: F405
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": True,
        },
        "app": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
