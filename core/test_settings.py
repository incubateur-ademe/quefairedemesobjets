from core.settings import *  # noqa: F403

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
    "database": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}

# Storages is defined in settings.py the undefined
# error can safely be ignored here
STORAGES["default"][  # noqa: F405
    "BACKEND"
] = "django.core.files.storage.InMemoryStorage"
