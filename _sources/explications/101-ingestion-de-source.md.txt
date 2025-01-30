# Ingestion des sources

## Étapes

1. Vérification de la configuration
1. Normalisation
1. Vérification de la données à ingérer normalisées
1. Comparaison avec les instances des acteurs en base de données pour déterminer les acteurs à modifier, créer ou supprimer
1. suite…

### Vérification de la configuration

La confiuration doit suivre le format de la class [DAGConfig](../../dags/sources/tasks/airflow_logic/config_management.py#DAGConfig)

### Normalisation

Les règles de nomalisation décrite dans le paramètre du DAG dans la section `normalization_rules`

les règles sont de différent type et appliquée dans l'ordre suivant:

1. Renommage des colonnes. Format : { "origin": "col origin", "destination": "col origin" }
1. Transformation des colonnes. Format : { "origin": "col origin", "destination": "col destination", "transformation": "function_name" }
1. Ajout des colonnes avec une valeur par défaut. Format : { "column": "col 1", "value" : "val" }
1. Transformation du dataframe. Format : { "origin": ["col origin 1", "col origin 2"], "transformation": "function_name", "destination": ["col destination 1", "col destination 2"] }
1. Supression des colonnes. Format : { "remove": "col 1" }
1. Colonnes à garder (rien à faire, utilisé pour le controle). Format : { "keep": "col 1" }

Après la normalisation, les données des acteurs sont très proches des données cibles:

- Les liens vers les autres tables sont représentés par les codes, i.e. les objets `actions`, `sous-catégories`, `label`, `acteur_type` et `label` sont représentés par leurs codes en liste ou valeur simple
- les données à ingérer sont comparables aux données en base de données
