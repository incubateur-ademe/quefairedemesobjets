# Déduplication d'acteurs

 - **QUOI**: une pipeline pour dédupliquer nos acteurs
 - **POURQUOI**: réduire les doublons sur la carte
 - **COMMENT**: sur la base d'un travail antérieur de clustering, on réutilise ou créer un "parent" existant (qui sera affiché sur la carte), et on attache les autres acteurs comme "enfants" (qui ne seront pas affichés sur la carte)

## Utilisation

 1. Définir les variables DB: `DB_URL_DEV`, `DB_URL_PREPROD` ou `DB_URL_PROD`
 2. Placer votre CSV de clustering dans ce dossier et adapter `CLUSTERING_CSV_FILEPATH`
 3. Mettre à jour `tests/verifications.py` au besoin
 4. Lancer le script `python acteur_deduplicate.py` et laisser vous guider