# Runs

Un dossier pour stocker les fichiers liés à chaque nouvelle déduplication

## Fichiers à fournir
 - `./{RUN_ID}/clusters.csv` = fichier de dédup,
    1 ligne = 1 cluster_id => identifiant_unique
 - `./{RUN_ID}/verifications.py` = liste de certains changements
    attendus selon le modèle Change

## Fichiers créés par le script
- `./{RUN_ID}/clusters_done_{db_env}.json`: liste des fichiers traités,
    par environement DB, pour pouvoir reprendre la progression en cas
    d'arrêt du script (ex: erreur, volonté de pauser et reprendre plus tard)