# ruff: noqa: F405
# F405 is suppressed because this file relies on star imports from base.py.
# All names (INSTALLED_APPS, MIDDLEWARE, BASE_URL, etc.) are defined
# in settings.base and intentionally re-used here.
from settings.base import *  # noqa: F403

# ---------------------------------------------------------------------------
# GeoDjango library paths
#
# Only set when the env var is explicitly provided (e.g. NixOS custom paths).
# If absent, Django falls back to its own discovery — no crash on stock macOS.
# ---------------------------------------------------------------------------
import decouple

GEOS_LIBRARY_PATH = decouple.config("GEOS_LIBRARY_PATH", default="", cast=str) or None
GDAL_LIBRARY_PATH = decouple.config("GDAL_LIBRARY_PATH", default="", cast=str) or None
