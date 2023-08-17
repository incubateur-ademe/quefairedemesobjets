"""
Django settings for quefairedemesobjets project.

Generated by 'django-admin startproject' using Django 4.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from contextlib import suppress
from pathlib import Path

import decouple
import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = decouple.config("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = decouple.config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = decouple.config("ALLOWED_HOSTS", default="localhost", cast=str).split(
    ","
)

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "explorer",
    "qfdmo",
]

if DEBUG:
    INSTALLED_APPS.extend(
        [
            "debug_toolbar",
            "django_browser_reload",
        ]
    )

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if DEBUG:
    MIDDLEWARE.extend(
        [
            "debug_toolbar.middleware.DebugToolbarMiddleware",
            "django_browser_reload.middleware.BrowserReloadMiddleware",
        ]
    )
with suppress(ModuleNotFoundError):
    from debug_toolbar.settings import CONFIG_DEFAULTS

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": "operator.truth",
        "HIDE_IN_STACKTRACES": CONFIG_DEFAULTS["HIDE_IN_STACKTRACES"] + ("sentry_sdk",),
    }

LOGLEVEL = decouple.config("LOGLEVEL", default="error", cast=str).upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOGLEVEL,
        },
    },
    "formatters": {
        "default": {
            # exact format is not important, this is the minimum information
            "format": "[%(asctime)s] %(name)-12s] %(levelname)-8s : %(message)s",
        },
    },
}

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "jinja2"],
        "OPTIONS": {
            "environment": "core.jinja2_handler.environment",
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASE_URL = decouple.config("DATABASE_URL")
default_settings = dj_database_url.parse(DATABASE_URL)
default_settings["ENGINE"] = "django.contrib.gis.db.backends.postgis"

# EXPLORER settings
# from https://django-sql-explorer.readthedocs.io/en/latest/install.html
# The readonly access is configured with fake access when DB_READONLY env
# variable is not set.
DB_READONLY = decouple.config(
    "DB_READONLY",
    cast=str,
    default="postgres://fakeusername:fakepassword@postgres:5432/database",
)
readonly_settings = dj_database_url.parse(DB_READONLY)

DATABASES = {"default": default_settings, "readonly": readonly_settings}

EXPLORER_CONNECTIONS = {"Default": "readonly"}
EXPLORER_DEFAULT_CONNECTION = "readonly"


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation"
        ".UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Redirect to home URL after login
LOGIN_REDIRECT_URL = "home:index"
LOGOUT_REDIRECT_URL = "home:homepage"

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "static" / "to_collect",
    BASE_DIR / "static" / "compiled",
]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
WHITENOISE_KEEP_ONLY_HASHED_FILES = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

sentry_sdk.init(
    dsn=decouple.config("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
    # trace only 1% of requests to get performance statistics
    traces_sample_rate=0.01,
    # By default the SDK will try to use the SENTRY_RELEASE
    # environment variable, or infer a git commit
    # SHA as release, however you may want to set
    # something more human-readable.
    # release="qfdmo@1.0.0",
)

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
