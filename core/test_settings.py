from core.settings import *  # noqa: F403

# Add test hosts to ALLOWED_HOSTS for integration tests
ALLOWED_HOSTS = [
    *ALLOWED_HOSTS,  # noqa: F405
    "lvao.ademe.fr",
    "quefairedemesdechets.ademe.fr",
]
CSRF_TRUSTED_ORIGINS = ["http://localhost"]

DATABASES = {
    "default": DATABASES["default"],  # noqa: F405
}

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
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
}

MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE  # noqa: F405
    if middleware
    not in [
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
]
