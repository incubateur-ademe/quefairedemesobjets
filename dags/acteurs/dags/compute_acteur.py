from datetime import timedelta

from acteurs.tasks.airflow_logic.check_model_table_consistency_task import (
    check_model_table_consistency_task,
)
from acteurs.tasks.airflow_logic.replace_acteur_table_task import (
    replace_acteur_table_task,
)
from airflow import DAG
from airflow.operators.bash import BashOperator
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}

dbt_run = "dbt run --select"
dbt_test = "dbt test --resource-type model --select"


with DAG(
    "compute_acteurs",
    default_args=default_args,
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
        bash_command=(f"{dbt_run} base.acteurs"),
    )
    dbt_test_base_acteurs = BashOperator(
        task_id="dbt_test_base_acteurs",
        bash_command=(f"{dbt_test} base.acteurs"),
    )

    dbt_run_intermediate_acteurs = BashOperator(
        task_id="dbt_run_intermediate_acteurs",
        bash_command=("dbt run --models intermediate.acteurs"),
    )
    dbt_test_intermediate_acteurs = BashOperator(
        task_id="dbt_test_intermediate_acteurs",
        bash_command=(f"{dbt_test} intermediate.acteurs"),
    )

    dbt_run_exposure_acteurs_common = BashOperator(
        task_id="dbt_run_exposure_acteurs_common",
        bash_command=(f"{dbt_run} exposure.acteurs.common"),
    )
    dbt_test_exposure_acteurs_common = BashOperator(
        task_id="dbt_test_exposure_acteurs_common",
        bash_command=(f"{dbt_test} exposure.acteurs.common"),
    )

    dbt_run_marts_acteurs_carte = BashOperator(
        task_id="dbt_run_marts_acteurs_carte",
        bash_command=(f"{dbt_run} marts.acteurs.carte"),
    )
    dbt_test_marts_acteurs_carte = BashOperator(
        task_id="dbt_test_marts_acteurs_carte",
        bash_command=(f"{dbt_test} marts.acteurs.carte"),
    )
    dbt_run_exposure_acteurs_carte = BashOperator(
        task_id="dbt_run_exposure_acteurs_carte",
        bash_command=(f"{dbt_run} exposure.acteurs.carte"),
    )
    dbt_test_exposure_acteurs_carte = BashOperator(
        task_id="dbt_test_exposure_acteurs_carte",
        bash_command=(f"{dbt_test} exposure.acteurs.carte"),
    )

    dbt_run_marts_acteurs_opendata = BashOperator(
        task_id="dbt_run_marts_acteurs_opendata",
        bash_command=(f"{dbt_run} marts.acteurs.opendata"),
    )
    dbt_test_marts_acteurs_opendata = BashOperator(
        task_id="dbt_test_marts_acteurs_opendata",
        bash_command=(f"{dbt_test} marts.acteurs.opendata"),
    )
    dbt_run_exposure_acteurs_opendata = BashOperator(
        task_id="dbt_run_exposure_acteurs_opendata",
        bash_command=(f"{dbt_run} exposure.acteurs.opendata"),
    )
    dbt_test_exposure_acteurs_opendata = BashOperator(
        task_id="dbt_test_exposure_acteurs_opendata",
        bash_command=(f"{dbt_test} exposure.acteurs.opendata"),
    )

    dbt_run_marts_acteurs_exhaustive = BashOperator(
        task_id="dbt_run_marts_acteurs_exhaustive",
        bash_command=(f"{dbt_run} marts.acteurs.exhaustive"),
    )
    dbt_test_marts_acteurs_exhaustive = BashOperator(
        task_id="dbt_test_marts_acteurs_exhaustive",
        bash_command=(f"{dbt_test} marts.acteurs.exhaustive"),
    )
    dbt_run_exposure_acteurs_exhaustive = BashOperator(
        task_id="dbt_run_exposure_acteurs_exhaustive",
        bash_command=(f"{dbt_run} exposure.acteurs.exhaustive"),
    )
    dbt_test_exposure_acteurs_exhaustive = BashOperator(
        task_id="dbt_test_exposure_acteurs_exhaustive",
        bash_command=(f"{dbt_test} exposure.acteurs.exhaustive"),
    )

    check_model_table_epci_task = check_model_table_consistency_task(
        dag, "qfdmo", "EPCI", "exposure_epci"
    )
    replace_epci_table_task = replace_acteur_table_task(
        dag, "qfdmo_", "exposure_", tables=["epci"]
    )

    check_model_table_displayedacteur_task = check_model_table_consistency_task(
        dag, "qfdmo", "DisplayedActeur", "exposure_carte_acteur"
    )
    check_model_table_displayedpropositionservice_task = (
        check_model_table_consistency_task(
            dag,
            "qfdmo",
            "DisplayedPropositionService",
            "exposure_carte_propositionservice",
        )
    )
    check_model_table_displayedperimetreadomicile_task = (
        check_model_table_consistency_task(
            dag,
            "qfdmo",
            "DisplayedPerimetreADomicile",
            "exposure_carte_perimetreadomicile",
        )
    )
    replace_displayedacteur_table_task = replace_acteur_table_task(
        dag, "qfdmo_displayed", "exposure_carte_"
    )

    check_model_table_vueacteur_task = check_model_table_consistency_task(
        dag, "qfdmo", "VueActeur", "exposure_exhaustive_acteur"
    )
    check_model_table_vuepropositionservice_task = check_model_table_consistency_task(
        dag,
        "qfdmo",
        "VuePropositionService",
        "exposure_exhaustive_propositionservice",
    )
    check_model_table_vueperimetreadomicile_task = check_model_table_consistency_task(
        dag, "qfdmo", "VuePerimetreADomicile", "exposure_exhaustive_perimetreadomicile"
    )
    replace_vueacteur_table_task = replace_acteur_table_task(
        dag, "qfdmo_vue", "exposure_exhaustive_"
    )

    # Définir la séquence principale
    (
        dbt_run_base_acteurs
        >> dbt_test_base_acteurs
        >> dbt_run_intermediate_acteurs
        >> dbt_test_intermediate_acteurs
        >> dbt_run_exposure_acteurs_common
        >> dbt_test_exposure_acteurs_common
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
    (dbt_test_exposure_acteurs_carte >> check_model_table_epci_task)
    (dbt_test_exposure_acteurs_exhaustive >> check_model_table_epci_task)
    # Définir la séquence de vérification en parallèle
    (check_model_table_epci_task >> replace_epci_table_task)
    (
        replace_epci_table_task
        >> check_model_table_displayedacteur_task
        >> check_model_table_displayedpropositionservice_task
        >> check_model_table_displayedperimetreadomicile_task
        >> replace_displayedacteur_table_task
        >> check_model_table_vueacteur_task
        >> check_model_table_vuepropositionservice_task
        >> check_model_table_vueperimetreadomicile_task
        >> replace_vueacteur_table_task
    )
