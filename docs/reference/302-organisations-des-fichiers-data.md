# Architecture des fichiers de code de la partie data

Appliqué plus spécifiquement lors de la réorganisation des fichiers des dags d'ingestion des sources

```txt
/dags                               -> A renommer
|- config
|- shared                           -> fichiers partagés par plusieurs sujets
   |- tasks                         -> taches commune à plusieurs sujets
      |- airflow_logic              -> logique propre à l'utilisation de airflow commune à plusieurs sujets
      |- business_logic             -> logique métier commune à plusieurs sujets
      |- database_logic             -> logique liée aux bases de données commune à plusieurs sujets
|- <sujet>                          -> fichiers spécifiques à chaque sujet (ex : source, compute_acteur…)
   |- dags                          -> dags relatif au sujet
   |- tasks                         -> taches utilisées par les dags relatif au sujet
      |- airflow_logic              -> logic propre à l'utilisation de airflow : déclaration des tacks et des wrapper
      |- business_logic             -> logique métier
      |- transform                  -> fonction de transformation de données
         |- transform_df            -> fonction de transformation des dataframe
         |- transform_column        -> fonction de transformation des colonnes des dataframe
|- utils                            -> utilitaire DÉPRÉCIÉ, à ranger dans l'arborescence ci-dessus
```

les tests suivent la même architecture que le dossier dags dans le dossier dags_unit_tests.
