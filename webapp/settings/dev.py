# ruff: noqa: F405
# F405 is suppressed because this file relies on star imports from base.py.
# All names (INSTALLED_APPS, MIDDLEWARE, BASE_URL, etc.) are defined
# in settings.base and intentionally re-used here.
from settings.base import *  # noqa: F403

import decouple
import os

# ---------------------------------------------------------------------------
# GeoDjango library paths
# ---------------------------------------------------------------------------
if "GDAL_LIBRARY_PATH" in os.environ:
    GDAL_LIBRARY_PATH = decouple.config(
        "GDAL_LIBRARY_PATH",
        default=None,
        cast=str,
    )

if "GEOS_LIBRARY_PATH" in os.environ:
    GEOS_LIBRARY_PATH = decouple.config(
        "GEOS_LIBRARY_PATH",
        cast=str,
    )

# ---------------------------------------------------------------------------
# Debug & developer conveniences
# ---------------------------------------------------------------------------
DEBUG = decouple.config("DEBUG", default=False, cast=bool)
STIMULUS_DEBUG = decouple.config("STIMULUS_DEBUG", default=False, cast=bool)
POSTHOG_DEBUG = decouple.config("POSTHOG_DEBUG", default=False, cast=bool)
BYPASS_ACTEUR_READONLY_FIELDS = decouple.config(
    "BYPASS_ACTEUR_READONLY_FIELDS", default=False, cast=bool
)

# Dev-only default for EMAIL_BACKEND — production overrides to SMTP.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SHELL_PLUS_PRINT_SQL = True

# ---------------------------------------------------------------------------
# Static & media files (local filesystem in dev)
# ---------------------------------------------------------------------------
MEDIA_ROOT = "media"
MEDIA_URL = "/media/"

# ---------------------------------------------------------------------------
# DEBUG-only additions
# ---------------------------------------------------------------------------
if DEBUG:
    # FIXME: A CSRF error can occur locally when using HTTPS — this workaround
    # is harmless for local dev but should eventually be fixed properly.
    CSRF_TRUSTED_ORIGINS = [BASE_URL]

    INSTALLED_APPS.extend(["django_browser_reload"])
    MIDDLEWARE.extend(
        [
            "django_browser_reload.middleware.BrowserReloadMiddleware",
        ]
    )

    if decouple.config("WITH_DJANGO_DEBUG_TOOLBAR", default=False, cast=bool):
        from debug_toolbar.settings import CONFIG_DEFAULTS

        INSTALLED_APPS.append("debug_toolbar")
        MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

        patterns_to_exclude = ["/lookbook"]

        def show_toolbar_callback(request):
            path_is_not_excluded = not any(
                p in request.path for p in patterns_to_exclude
            )
            if request.headers.get("User-Agent") == "playwright":
                return False
            if request.headers.get("Sec-Fetch-Dest") == "iframe":
                return False
            return path_is_not_excluded

        DEBUG_TOOLBAR_CONFIG = {
            "DISABLE_PANELS": (
                "debug_toolbar.panels.request.RequestPanel",
                "debug_toolbar.panels.staticfiles.StaticFilesPanel",
                "debug_toolbar.panels.alerts.AlertsPanel",
                "debug_toolbar.panels.cache.CachePanel",
                "debug_toolbar.panels.signals.SignalsPanel",
                "debug_toolbar.panels.community.CommunityPanel",
                "debug_toolbar.panels.redirects.RedirectsPanel",
                "debug_toolbar.panels.profiling.ProfilingPanel",
            ),
            "TOOLBAR_STORE_CLASS": "debug_toolbar.store.DatabaseStore",
            "SHOW_TOOLBAR_CALLBACK": show_toolbar_callback,
            "HIDE_IN_STACKTRACES": CONFIG_DEFAULTS["HIDE_IN_STACKTRACES"]
            + ("sentry_sdk",),
            "ROOT_TAG_EXTRA_ATTRS": "data-turbo-permanent",
        }

    if decouple.config("WITH_DJANGO_SILK", default=False, cast=bool):
        INSTALLED_APPS.append("silk")
        MIDDLEWARE.append("silk.middleware.SilkyMiddleware")

    CORS_ALLOW_ALL_ORIGINS = True
