## Organisation du dossier `dags`

Appliqué plus spécifiquement lors de la réorganisation des fichiers des dags d'ingestion des sources

```
/dags
|- config
|- source                           -> fichiers spécifique à l'ingestion des sources
   |- dags                          -> dags d'ingestion des sources
   |- tasks                         -> taches utilisées par les dags d'injestion des sources
      |- airflow_logic              -> logic propre à l'utilisation de airflow : déclaration des tacks et des wrapper
      |- business_logic             -> logique métier
      |- transform                  -> fonction de transformation de données
         |- transform_df            -> fonction de transformation des dataframe
         |- transform_column        -> fonction de transformation des colonnes des dataframe
|- tasks                            -> taches commune aux dags ayant différents propos
   |- airflow_logic                 -> logic propre à l'utilisation de airflow commune aux dags ayant différents propos
   |- business_logic                -> logique métier commune aux dags ayant différents propos
   |- …
|- utils                            -> utilitaire DÉPRÉCIÉ, à ranger dans l'arborescence ci-dessus
```

les tests suivent la même architecture que le dossier dags dans le dossier dags_unit_tests.
