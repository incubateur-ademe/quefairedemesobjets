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
from import_export.formats.base_formats import CSV, XLS, XLSX
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = decouple.config("SECRET_KEY")

BASE_URL = decouple.config("BASE_URL", default="http://localhost:8000")
CMS_BASE_URL = decouple.config(
    "CMS_BASE_URL", default="https://longuevieauxobjets.ademe.fr"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = decouple.config("DEBUG", default=False, cast=bool)
STIMULUS_DEBUG = decouple.config("STIMULUS_DEBUG", default=False, cast=bool)
POSTHOG_DEBUG = decouple.config("POSTHOG_DEBUG", default=False, cast=bool)

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
    "django.contrib.sitemaps",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django_extensions",
    "explorer",
    "import_export",
    "widget_tweaks",
    "dsfr",
    "django.forms",
    "colorfield",
    "core",
    "qfdmd",
    "qfdmo",
    "corsheaders",
]

# FIXME : check if we can manage django forms templating with jinja2
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"


if DEBUG:
    INSTALLED_APPS.extend(["debug_toolbar", "django_browser_reload"])
    MEDIA_ROOT = "media"
    MEDIA_URL = "/media/"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "database": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "lvao_django_cache",
    },
}

X_FRAME_OPTIONS = "ALLOWALL"

CORS_ALLOWED_ORIGINS = decouple.config(
    "CORS_ALLOWED_ORIGINS", default="https://quefairedemesdechets.ademe.fr", cast=str
).split(",")

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/deploy-preview-\d*--quefairedemesdechets\.netlify\.app$",
]

if DEBUG:
    MIDDLEWARE.extend(
        [
            "debug_toolbar.middleware.DebugToolbarMiddleware",
            "django_browser_reload.middleware.BrowserReloadMiddleware",
        ]
    )

    CORS_ALLOW_ALL_ORIGINS = DEBUG

with suppress(ModuleNotFoundError):
    from debug_toolbar.settings import CONFIG_DEFAULTS

    patterns_to_exclude = [
        "/test_iframe",
    ]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: not any(
            p in request.path for p in patterns_to_exclude
        ),
        "HIDE_IN_STACKTRACES": CONFIG_DEFAULTS["HIDE_IN_STACKTRACES"] + ("sentry_sdk",),
    }

LOGLEVEL = decouple.config(
    "LOGLEVEL", default="info" if DEBUG else "error", cast=str
).upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"hide_staticfiles": {"()": "core.logging.SkipStaticFilter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "filters": ["hide_staticfiles"] if DEBUG else [],
        }
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOGLEVEL,
        },
        "qfdmo": {
            "handlers": ["console"],
            "level": LOGLEVEL,
        },
    },
    "formatters": {
        "default": {
            # exact format is not important, this is the minimum information
            "format": "[%(asctime)s] [%(name)s] [%(levelname)s] : %(message)s",
        },
    },
}

ROOT_URLCONF = "core.urls"


def context_processors():
    return [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "core.context_processors.environment",
        "core.context_processors.content",
        "core.context_processors.assistant",
        "dsfr.context_processors.site_config",
    ]


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "jinja2"],
        "OPTIONS": {
            "environment": "core.jinja2_handler.environment",
            "context_processors": context_processors(),
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": context_processors()},
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASE_URL = decouple.config(
    "DATABASE_URL",
    default="postgis://qfdmo:qfdmo@localhost:6543/qfdmo",  # pragma: allowlist secret  # noqa: E501
)
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

DATABASES = {
    "default": default_settings,
    "readonly": readonly_settings,
}

EXPLORER_CONNECTIONS = {"Default": "readonly"}
EXPLORER_DEFAULT_CONNECTION = "readonly"

CONN_HEALTH_CHECKS = True
CONN_MAX_AGE = decouple.config("CONN_MAX_AGE", cast=int, default=0)

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
# Renvoyer vers l'admin'
LOGOUT_REDIRECT_URL = "qfdmo:login"
LOGIN_URL = "qfdmo:login"

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


WHITENOISE_KEEP_ONLY_HASHED_FILES = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ENVIRONMENT = decouple.config("ENVIRONMENT", default="development", cast=str)

sentry_sdk.init(
    dsn=decouple.config("SENTRY_DSN", cast=str, default=""),
    integrations=[DjangoIntegration()],
    environment=ENVIRONMENT,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=False,
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

DEFAULT_ACTION_DIRECTION = "jai"

INSEE_KEY = decouple.config("INSEE_KEY", cast=str, default="")
INSEE_SECRET = decouple.config("INSEE_SECRET", cast=str, default="")


DEFAULT_MAX_SOLUTION_DISPLAYED = decouple.config(
    "DEFAULT_MAX_SOLUTION_DISPLAYED", cast=int, default=10
)
CARTE_MAX_SOLUTION_DISPLAYED = decouple.config(
    "CARTE_MAX_SOLUTION_DISPLAYED", cast=int, default=100
)
DISTANCE_MAX = decouple.config("DISTANCE_MAX", cast=int, default=30000)

DJANGO_IMPORT_EXPORT_LIMIT = decouple.config(
    "DJANGO_IMPORT_EXPORT_LIMIT", cast=int, default=1000
)

NB_CORRECTION_DISPLAYED = decouple.config(
    "NB_CORRECTION_DISPLAYED", cast=int, default=100
)

SHELL_PLUS_PRINT_SQL = True

# Object storage with Scaleway
AWS_ACCESS_KEY_ID = decouple.config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = decouple.config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = decouple.config("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = decouple.config("AWS_S3_REGION_NAME", default="")
AWS_S3_ENDPOINT_URL = decouple.config("AWS_S3_ENDPOINT_URL", default="")


STORAGES = {
    "default": {
        "BACKEND": (
            "storages.backends.s3.S3Storage"
            if AWS_ACCESS_KEY_ID
            else "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AIRFLOW_WEBSERVER_REFRESHACTEUR_URL = decouple.config(
    "AIRFLOW_WEBSERVER_REFRESHACTEUR_URL", cast=str, default="http://localhost:8080"
)

USE_I18N = True
LANGUAGE_CODE = "fr-fr"

IMPORT_EXPORT_TMP_STORAGE_CLASS = "import_export.tmp_storages.MediaStorage"
IMPORT_FORMATS = [CSV, XLSX, XLS]
ADDRESS_SUGGESTION_FORM = decouple.config(
    "ADDRESS_SUGGESTION_FORM", default="https://tally.so/r/wzy9ZZ", cast=str
)
UPDATE_SUGGESTION_FORM = decouple.config(
    "UPDATE_SUGGESTION_FORM", default="https://tally.so/r/3xMqd9", cast=str
)

FEEDBACK_FORM = decouple.config(
    "FEEDBACK_FORM", default="https://tally.so/r/3EW88q", cast=str
)
CONTACT_FORM = decouple.config(
    "CONTACT_FORM", default="https://tally.so/r/wzYveR", cast=str
)

ASSISTANT_SURVEY_FORM = decouple.config(
    "ASSISTANT_SURVEY_FORM", default="https://tally.so/r/wvNgx0", cast=str
)

QFDMO_GOOGLE_SEARCH_CONSOLE = "google9dfbbc61adbe3888.html"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
ASSISTANT = {
    "MATOMO_ID": decouple.config("ASSISTANT_MATOMO_ID", default=82, cast=int),
    "POSTHOG_KEY": decouple.config(
        "ASSISTANT_POSTHOG_KEY",
        default="phc_fSfhoWDOUxZdKWty16Z3XfRiAoWd1qdJK0N0z9kQHJr",  # pragma: allowlist secret  # noqa: E501
        cast=str,
    ),
}
