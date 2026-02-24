from acteurs.tasks.airflow_logic.check_model_table_consistency_task import (
    check_model_table_consistency_task,
)
from acteurs.tasks.airflow_logic.replace_acteur_table_task import (
    replace_acteur_table_task,
)
from airflow import DAG
from airflow.operators.bash import BashOperator
from shared.config.airflow import DEFAULT_ARGS
from shared.config.dbt_commands import DBT_RUN, DBT_TEST
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    "compute_acteurs",
    default_args=DEFAULT_ARGS,
    schedule=SCHEDULES.EVERY_DAY_AT_00_00,
    start_date=START_DATES.DEFAULT,
    dag_display_name="Acteurs affichés - Rafraîchir les acteurs affichés",
    description=(
        "Ce DAG construit les tables des acteurs utilisables par l'admin"
        " (vue exhaustive des acteurs), par la carte (vue des acteurs affichés) et"
        " par l'export des acteurs en open-data."
    ),
    tags=[TAGS.COMPUTE, TAGS.ACTEURS, TAGS.CARTE, TAGS.OPENDATA, TAGS.DBT],
    max_active_runs=1,
) as dag:
    dbt_run_base_acteurs = BashOperator(
        task_id="dbt_run_base_acteurs",
        bash_command=(f"{DBT_RUN} base.acteurs"),
    )
    dbt_test_base_acteurs = BashOperator(
        task_id="dbt_test_base_acteurs",
        bash_command=(f"{DBT_TEST} base.acteurs"),
    )

    dbt_run_intermediate_acteurs = BashOperator(
        task_id="dbt_run_intermediate_acteurs",
        bash_command=("dbt run --models intermediate.acteurs"),
    )
    dbt_test_intermediate_acteurs = BashOperator(
        task_id="dbt_test_intermediate_acteurs",
        bash_command=(f"{DBT_TEST} intermediate.acteurs"),
    )

    dbt_run_marts_acteurs_carte = BashOperator(
        task_id="dbt_run_marts_acteurs_carte",
        bash_command=(f"{DBT_RUN} marts.acteurs.carte"),
    )
    dbt_test_marts_acteurs_carte = BashOperator(
        task_id="dbt_test_marts_acteurs_carte",
        bash_command=(f"{DBT_TEST} marts.acteurs.carte"),
    )
    dbt_run_exposure_acteurs_carte = BashOperator(
        task_id="dbt_run_exposure_acteurs_carte",
        bash_command=(f"{DBT_RUN} exposure.acteurs.carte"),
    )
    dbt_test_exposure_acteurs_carte = BashOperator(
        task_id="dbt_test_exposure_acteurs_carte",
        bash_command=(f"{DBT_TEST} exposure.acteurs.carte"),
    )

    dbt_run_marts_acteurs_opendata = BashOperator(
        task_id="dbt_run_marts_acteurs_opendata",
        bash_command=(f"{DBT_RUN} marts.acteurs.opendata"),
    )
    dbt_test_marts_acteurs_opendata = BashOperator(
        task_id="dbt_test_marts_acteurs_opendata",
        bash_command=(f"{DBT_TEST} marts.acteurs.opendata"),
    )
    dbt_run_exposure_acteurs_opendata = BashOperator(
        task_id="dbt_run_exposure_acteurs_opendata",
        bash_command=(f"{DBT_RUN} exposure.acteurs.opendata"),
    )
    dbt_test_exposure_acteurs_opendata = BashOperator(
        task_id="dbt_test_exposure_acteurs_opendata",
        bash_command=(f"{DBT_TEST} exposure.acteurs.opendata"),
    )

    dbt_run_marts_acteurs_exhaustive = BashOperator(
        task_id="dbt_run_marts_acteurs_exhaustive",
        bash_command=(f"{DBT_RUN} marts.acteurs.exhaustive"),
    )
    dbt_test_marts_acteurs_exhaustive = BashOperator(
        task_id="dbt_test_marts_acteurs_exhaustive",
        bash_command=(f"{DBT_TEST} marts.acteurs.exhaustive"),
    )
    dbt_run_exposure_acteurs_exhaustive = BashOperator(
        task_id="dbt_run_exposure_acteurs_exhaustive",
        bash_command=(f"{DBT_RUN} exposure.acteurs.exhaustive"),
    )
    dbt_test_exposure_acteurs_exhaustive = BashOperator(
        task_id="dbt_test_exposure_acteurs_exhaustive",
        bash_command=(f"{DBT_TEST} exposure.acteurs.exhaustive"),
    )

    check_model_table_displayedacteur_task = check_model_table_consistency_task(
        "qfdmo", "DisplayedActeur", "exposure_carte_acteur"
    )
    check_model_table_displayedpropositionservice_task = (
        check_model_table_consistency_task(
            "qfdmo",
            "DisplayedPropositionService",
            "exposure_carte_propositionservice",
        )
    )
    check_model_table_displayedperimetreadomicile_task = (
        check_model_table_consistency_task(
            "qfdmo",
            "DisplayedPerimetreADomicile",
            "exposure_carte_perimetreadomicile",
        )
    )
    replace_displayedacteur_table_task = replace_acteur_table_task(
        "qfdmo_displayed", "exposure_carte_"
    )

    check_model_table_vueacteur_task = check_model_table_consistency_task(
        "qfdmo", "VueActeur", "exposure_exhaustive_acteur"
    )
    check_model_table_vuepropositionservice_task = check_model_table_consistency_task(
        "qfdmo",
        "VuePropositionService",
        "exposure_exhaustive_propositionservice",
    )
    check_model_table_vueperimetreadomicile_task = check_model_table_consistency_task(
        "qfdmo", "VuePerimetreADomicile", "exposure_exhaustive_perimetreadomicile"
    )
    replace_vueacteur_table_task = replace_acteur_table_task(
        "qfdmo_vue", "exposure_exhaustive_"
    )

    # Définir la séquence principale
    (
        dbt_run_base_acteurs
        >> dbt_test_base_acteurs
        >> dbt_run_intermediate_acteurs
        >> dbt_test_intermediate_acteurs
        >> dbt_run_marts_acteurs_carte
        >> dbt_test_marts_acteurs_carte
        >> dbt_run_exposure_acteurs_carte
        >> dbt_test_exposure_acteurs_carte
        >> dbt_run_marts_acteurs_opendata
        >> dbt_test_marts_acteurs_opendata
        >> dbt_run_exposure_acteurs_opendata
        >> dbt_test_exposure_acteurs_opendata
        >> dbt_run_marts_acteurs_exhaustive
        >> dbt_test_marts_acteurs_exhaustive
        >> dbt_run_exposure_acteurs_exhaustive
        >> dbt_test_exposure_acteurs_exhaustive
    )
    # Définir la séquence de vérification en parallèle
    (
        dbt_test_exposure_acteurs_carte
        >> check_model_table_displayedacteur_task
        >> check_model_table_displayedpropositionservice_task
        >> check_model_table_displayedperimetreadomicile_task
        >> replace_displayedacteur_table_task
    )
    (
        dbt_test_exposure_acteurs_exhaustive
        >> check_model_table_vueacteur_task
        >> check_model_table_vuepropositionservice_task
        >> check_model_table_vueperimetreadomicile_task
        >> replace_vueacteur_table_task
    )
