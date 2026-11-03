"""Static files storage aware of Parcel chunks.

Parcel's runtime loads lazy chunks (`maplibre-gl.1ea7348e.js`) by a name
written in the bundle, which the manifest storage does not rewrite: once
renamed with Django's hash and the original deleted, they would answer 404 in
production. This adds that reference to the rewritten patterns; a missing
chunk makes `collectstatic` fail.
"""

from whitenoise.storage import CompressedManifestStaticFilesStorage

PARCEL_CHUNK = r"""(?P<matched>"(?P<url>[\w.-]+\.[a-f0-9]{8}\.(?:js|css))")"""


class ParcelManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    patterns = CompressedManifestStaticFilesStorage.patterns + (
        ("*.js", ((PARCEL_CHUNK, '"%(url)s"'),)),
    )
