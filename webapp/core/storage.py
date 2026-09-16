"""Static files storage aware of Parcel chunks.

Parcel already names its chunks after their content hash
(`maplibre-gl.1ea7348e.js`) and its runtime loads them by that name, appended
to the URL of the current bundle: this is not an `import` Django knows how to
rewrite. Yet `ManifestStaticFilesStorage` renames every file with its own
hash, and `WHITENOISE_KEEP_ONLY_HASHED_FILES` deletes the original. In
production, every lazily loaded chunk would answer 404, while working under
`runserver`, which serves the original files.

This storage adds a rewrite pattern for those references: the name of a
chunk, between double quotes, in a JavaScript file. The pattern is narrow (a
name ending with eight hexadecimal characters then `.js` or `.css`) to only
touch what Parcel produces.

A reference to a chunk that does not exist makes `collectstatic` fail, as any
broken reference does under the manifest storage: the deploy stops rather
than shipping a 404.
"""

from whitenoise.storage import CompressedManifestStaticFilesStorage

PARCEL_CHUNK = r"""(?P<matched>"(?P<url>[\w.-]+\.[a-f0-9]{8}\.(?:js|css))")"""


class ParcelManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    patterns = CompressedManifestStaticFilesStorage.patterns + (
        ("*.js", ((PARCEL_CHUNK, '"%(url)s"'),)),
    )
