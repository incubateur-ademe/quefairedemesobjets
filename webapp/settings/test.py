# flake8: noqa: F405, F403
import os

# Tests (webapp + data-platform) must not require django-debug-toolbar /
# django-browser-reload. If DEBUG=True comes from the environment, settings.base
# would register those apps before this module loads; force DEBUG off first.
os.environ["DEBUG"] = "false"

from settings.base import *

import decouple

GEOS_LIBRARY_PATH = decouple.config("GEOS_LIBRARY_PATH", default="", cast=str) or None
GDAL_LIBRARY_PATH = decouple.config("GDAL_LIBRARY_PATH", default="", cast=str) or None

# Add test hosts to ALLOWED_HOSTS for integration tests
ALLOWED_HOSTS = ALLOWED_HOSTS + [
    "lvao.ademe.fr",
    "quefairedemesdechets.ademe.fr",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
    "database": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}

# Run background tasks synchronously in tests so assertions see their effects.
# ENQUEUE_ON_COMMIT=False is required: pytest wraps each test in a transaction
# that never commits, so on-commit enqueueing would never fire.
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.immediate.ImmediateBackend",
        "ENQUEUE_ON_COMMIT": False,
    }
}

STORAGES["default"]["BACKEND"] = "django.core.files.storage.InMemoryStorage"
STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
}

MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE
    if middleware
    not in [
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
]
