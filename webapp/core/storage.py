"""Stockage des statiques conscient des chunks Parcel.

Parcel nomme déjà ses chunks par le hachage de leur contenu
(`maplibre-gl.1ea7348e.js`) et son runtime les charge par ce nom, en le
concaténant à l'URL du bundle courant : ce n'est pas un `import` que Django
saurait réécrire. Or `ManifestStaticFilesStorage` renomme chaque fichier avec
son propre hachage, et `WHITENOISE_KEEP_ONLY_HASHED_FILES` supprime l'original.
En production, chaque chunk chargé à la demande répondrait donc 404 — tout en
marchant sous `runserver`, qui sert les fichiers d'origine.

Ce stockage ajoute un motif de réécriture pour ces références : le nom d'un
chunk, entre guillemets, dans un fichier JavaScript. Le motif est étroit — un
nom se terminant par huit caractères hexadécimaux puis `.js` ou `.css` — pour
ne toucher que ce que Parcel produit.
"""

from whitenoise.storage import CompressedManifestStaticFilesStorage

CHUNK_PARCEL = r"""(?P<matched>"(?P<url>[\w.-]+\.[a-f0-9]{8}\.(?:js|css))")"""


class ParcelManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    patterns = CompressedManifestStaticFilesStorage.patterns + (
        ("*.js", ((CHUNK_PARCEL, '"%(url)s"'),)),
    )
