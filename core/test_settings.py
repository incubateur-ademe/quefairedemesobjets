# flake8: noqa: F405, F403
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
