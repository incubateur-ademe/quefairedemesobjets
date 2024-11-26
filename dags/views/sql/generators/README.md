# Générateur SQL

 - **QUOI**: solution pour gérer le SQL des vues crées par les DAGs
 - **POURQUOI**: pour des raisons de fiablité et séparation des préoccupations:
    - Les DAG ne doivent pas générer le SQL des vues, mais utiliser du SQL prégénéré
    - Pour que les DAGs reposent sur du SQL testé et versionné
    (ce qu'on ne peut pas avoir si on est en full dynamique Python -> SQL -> CREATE dans le DAG)
 - **COMMENT**: en suivant les étapes suivantes:
    1. Fichier générateur SQL: `/views/sql/generators/{dag}_sql_generate.py`
    2. Fichier SQL: `/views/sql/{dag}.sql`
    3. Fichier DAG: `/views/{dag}.py` qui vient lire le SQL ci-dessus
    note: techniquement il faut d'abord définir la constante `VIEW_NAME` dans `/views/{dag}.py` avant pour la réutiliser dans l'étape 1.


Cette solution custom en attendant de voir si cela vaut le coup d'introduire des frameworks dédiés à la gestion des vues (ex: `dbt`)