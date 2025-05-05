# Migration airflow v3

## 🗺️ Contexte

- On utilise actuellement Airflow v2 alors que v3 est disponible depuis le 22 avril 2025

## 💡Pourquoi migrer?

Autre raison évidente que v3 doit être mieux que v2 sur le long terme:

- 🐞 **Correctif pour bug limitant le clustering**: [voir rapport du bug corrigé en v3](https://github.com/apache/airflow/discussions/46475), ceci fait référence à la limitation clustering où on ne peut pas définir un ordre précis pour l’enrichissement
- 🔢 **Versionnage des DAGs**: on a eu des cas par le passé de regressions sur nos DAG qui bloquaient le métier, le métier pourra via la UI rétrograder à une version antérieur qui fonctionne sans avoir à attendre une mise en prod
- 💽 **La vue d’ensemble assets:** ([datasets](https://airflow.apache.org/docs/apache-airflow/2.10.5/authoring-and-scheduling/datasets.html) en v2) qui devient maintenant partie intégrale de la UI (avant caché dans le menu supérieur) et qui va permettre d’avoir une **vue data-centrique (= QUOI)** de notre orchestration plus importantes que les détails techniques des DAGs (= COMMENT), notamment pour **aider le métier à comprendre** la data qu’on gère ET **faciliter la gestion des dépendances entre DAGs**
- 🚀 **Une UI plus responsive** (via AJAX qui ne recharge pas tout) pour être plus productif

## 🏗️ Comment migrer

Recommendation:

1. ✅ **Tests de bout en bout (e2e):** prendre le temps (ex: 1 semaine) pour écrire des tests en bout-en-bout sur les DAG eux-même
    - [Voir exemple](https://github.com/incubateur-ademe/quefairedemesobjets/tree/main/dags_unit_tests/e2e)
    - A chacune des étapes suivante on pourra rejouer les tests e2e et confirmer la non-regression de l’ensemble des DAGs
2. 🔌 **Migrer vers l’API [TaskFlow](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html)**: pour **réduire la quantité de code existante** et se préparer à l’avenir
    - ex: actuellement avec PythonOperator **on doit gérer les XCOM manuellement** ce qui n’est pas le cas en TaskFlow
3. 📂 **Restructurer les dossiers** de la manière suivante: ceci notamment pour réduire les temps de crawl de l’intégralite du dossier DAG et mieux organiser le code

    ```bash
    pipelines/
        dags/ # uniquement les fichiers pure DAGs
    	tasks/ # tâches réutilisées par les DAGs
    	business/ # logique business
    	# autres dossiers Airflow (ex: logs/)
    	tests/
    	    setup/ # ex: compatibilité pandas vs. SQLAlchemy vs. scikitlearn
    	    e2e/
    	    unit/
    	    performance/ # comparer perfs différentes méthodes (ex: pytest-benchmark)
    ```

4. 🐋 **Utiliser la nouvelle image docker v3** en montant uniquement `pipelines/dags` sur `$AIRFLOW_HOME/dags`