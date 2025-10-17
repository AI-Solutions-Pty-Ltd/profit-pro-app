import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
AUTH_USER_MODEL = "Account.Account"

# Authentication settings
LOGIN_URL = "login"  # Redirect to login page when authentication is required
LOGIN_REDIRECT_URL = "home"  # Redirect to home after successful login
LOGOUT_REDIRECT_URL = "home"  # Redirect to home after logout

SITE_ID = 1
SITE_NAME = os.getenv("SITE_NAME", "Profit Pro")
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

CORE_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_cleanup.apps.CleanupConfig",
    "django.contrib.sites",
    "app.core",
    "app.utils",
]

THIRD_PARTY_APPS = [
    "import_export",
    "phonenumber_field",
    "django_extensions",
    "tailwind",
    "crispy_forms",
    "crispy_tailwind",
    "app.theme",
    "heroicons",
    "django_filters",
    "mathfilters",
    # Core/shared apps
]

SHARED_APPS = [
    "app.Account",
    "app.Consultant",
    "app.Project",
    "app.BillOfQuantities",
]

INSTALLED_APPS = CORE_APPS + THIRD_PARTY_APPS + SHARED_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

ROOT_URLCONF = "app.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "app",
            BASE_DIR / "app" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "builtins": [
                "django.templatetags.static",
                "django.contrib.humanize.templatetags.humanize",
                "heroicons.templatetags.heroicons",
                "crispy_forms.templatetags.crispy_forms_tags",
                "app.core.templatetags.template_extras",
                "mathfilters.templatetags.mathfilters",
            ],
        },
    },
]

WSGI_APPLICATION = "app.core.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },  # TODO: This one is actually not working, do we want it anyway?
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "app.core.Utilities.validators.UppercaseValidator",
    },
    {
        "NAME": "app.core.Utilities.validators.LowercaseValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = os.getenv("STATIC_URL", "/static/")
# STATICFILES_DIRS = [BASE_DIR / "core" / "static/",]
STATIC_ROOT = os.getenv(
    "STATIC_ROOT", BASE_DIR / "staticfiles"
)  # collectstatic / Linux

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PHONENUMBER_DEFAULT_FORMAT = "NATIONAL"
PHONENUMBER_DB_FORMAT = "NATIONAL"
PHONENUMBER_DEFAULT_REGION = "ZA"

USE_EMAIL = os.getenv("USE_EMAIL", "").lower() in ("true", "1", "yes", "on")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "").lower() in ("true", "1", "yes", "on")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "").lower() in ("true", "1", "yes", "on")

# Email settings
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")
DEFAULT_EMAIL_HOST = os.getenv("DEFAULT_EMAIL_HOST", "")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))  # Default to standard TLS port
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")


CONTACT_EMAIL = os.getenv(
    "CONTACT_EMAIL", ADMIN_EMAIL or DEFAULT_FROM_EMAIL or "support@example.com"
)

# Crispy Forms Configuration
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Tailwind Configuration
TAILWIND_APP_NAME = "app.theme"
NPM_BIN_PATH = os.getenv("NPM_BIN_PATH", "C:/Program Files/nodejs/npm.cmd")
