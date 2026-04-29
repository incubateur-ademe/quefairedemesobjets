# flake8: noqa: F405, F403
import os

# Tests (webapp + data-platform) must not require django-debug-toolbar /
# django-browser-reload. If DEBUG=True comes from the environment, core.settings
# would register those apps before this module loads; force DEBUG off first.
os.environ["DEBUG"] = "false"

from core.settings import *

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
    # Mirror the named cache from core.settings so callers using
    # caches["actions"] don't fall over in tests.
    "actions": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
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
