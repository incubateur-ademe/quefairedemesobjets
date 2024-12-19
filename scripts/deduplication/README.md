# Déduplication d'acteurs

 - **QUOI**: une pipeline pour dédupliquer nos acteurs
 - **POURQUOI**: réduire les doublons sur la carte
 - **COMMENT**: sur la base d'un travail antérieur de clustering, on réutilise ou crée un "parent" existant (qui sera affiché sur la carte), et on attache les autres acteurs comme "enfants" (qui ne seront pas affichés sur la carte)

## Utilisation

 1. Créer un dossier sous `./runs/{RUN_ID}` (voir [README](./runs/README.md) pour les fichiers attendus)
 2. Changer les paramètres `RUN_*` dans `deduplicate.py`
 3. Lancer `python scripts/deduplication/deduplicate.py` et laisser vous guider
    on lance depuis la racine pour que les imports django qfdmo fonctionnent