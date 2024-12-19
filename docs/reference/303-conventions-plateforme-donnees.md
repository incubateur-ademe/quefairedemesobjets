# Conventions de la plateform données

**Statut : ❓ À approuver**

## Nommage des taches

les préfixes suivants sont appliqués sur le nom des taches :

- `load_` pour taches en charge de la lecture de données en base de données, sur des fichiers, via des api
- `db_data_` pour les tâches en charge de l'écriture

Eviter les prefix `_updated` ou `_merged` qui ne décrivent pas la donnée de la variable mais décrit l'action précédente qui a été réalisée

## Glossaire des noms courts

Pour limiter la taille des variables et des noms de fonctions, on utilise les noms courts suivants :

- `ps` : propositions de service (propositionservice)
- `rps` : propositions de service corrigées (revisionpropositionservice)
- `dps` : propositions de service affichées (displayedpropositionservice)
- `sscat` : sous catégories
