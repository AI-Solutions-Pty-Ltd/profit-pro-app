from settings.base import *  # noqa
from settings.base import BASE_DIR

DEBUG = True
SECRET_KEY = "django-insecure-l^sjb(j9w-3fe0+!qiu!j7c&bu!vrv=m@#1e6zwuwfqbm35v!i"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

ALLOWED_HOSTS = ["testserver"]

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = ""
DEFAULT_EMAIL_HOST = ""
EMAIL_HOST = ""
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_PORT = 587
ADMIN_EMAIL = ""
