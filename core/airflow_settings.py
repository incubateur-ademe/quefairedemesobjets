from core.settings import *  # noqa: F403

# Inactive the logging when Django is use in Airflow because it's not compatible
# with the Airflow logging system when saving logs to s3 storage
LOGGING_CONFIG = None

# Minimal Django apps required for ORM functionality in Airflow
INSTALLED_APPS = [
    # Django core apps required for ORM
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.gis",
    # Wagtail dependencies (required by qfdmo.models.config)
    # because it is used un carte_config as decorator
    "taggit",
    "modelcluster",
    "wagtail",
    "wagtail.snippets",
    "wagtail.search",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.images",
    "wagtail.documents",
    # Our business apps that contain the models we need
    "core",
    "qfdmo",
    "data",
]

# Minimal middleware for Airflow (no web requests to handle)
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]
