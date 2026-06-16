from core.settings.base import *  # noqa: F403

import decouple

# GeoDjango library paths - read from environment (useful when managed by homebrew, nix)
GDAL_LIBRARY_PATH = decouple.config(
    "GDAL_LIBRARY_PATH",
    default=None,
    cast=str,
)
GEOS_LIBRARY_PATH = decouple.config(
    "GEOS_LIBRARY_PATH",
    default=None,
    cast=str,
)
