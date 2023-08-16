from contextlib import suppress

import pytest


@pytest.fixture(autouse=True)
def disable_whitenoise(settings):
    settings.STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        }
    }
    settings.MIDDLEWARE = [
        middleware
        for middleware in settings.MIDDLEWARE
        if middleware != "whitenoise.middleware.WhiteNoiseMiddleware"
    ]


@pytest.fixture(autouse=True)
def disable_debug_toolbar(settings):
    with suppress(ValueError):
        settings.MIDDLEWARE.remove("debug_toolbar.middleware.DebugToolbarMiddleware")
