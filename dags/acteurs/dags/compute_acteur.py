from datetime import timedelta

import pendulum
from acteurs.tasks.airflow_logic.check_model_table_consistency_task import (
    check_model_table_consistency_task,
)
from acteurs.tasks.airflow_logic.replace_acteur_table_task import (
    replace_acteur_table_task,
)
from airflow import DAG
from airflow.operators.bash import BashOperator
from shared.config.schedules import SCHEDULES

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": pendulum.today("UTC").add(days=-1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    "compute_acteurs",
    default_args=default_args,
    dag_display_name="DBT - Rafraîchir les acteurs affichés",
    description=(
        "Ce DAG construit les tables des acteurs utilisables par l'admin"
        " (vue exhaustive des acteurs), par la carte (vue des acteurs affichés) et"
        " par l'export des acteurs en open-data."
    ),
    schedule=SCHEDULES.DAILY,
    max_active_runs=1,
) as dag:
    dbt_run_base_acteurs = BashOperator(
        task_id="dbt_run_base_acteurs",
        bash_command=("dbt run --models base.acteurs"),
    )
    dbt_test_base_acteurs = BashOperator(
        task_id="dbt_test_base_acteurs",
        bash_command=("dbt test --models base.acteurs"),
    )
    dbt_run_intermediate_acteurs = BashOperator(
        task_id="dbt_run_intermediate_acteurs",
        bash_command=("dbt run --models intermediate.acteurs"),
    )
    dbt_test_intermediate_acteurs = BashOperator(
        task_id="dbt_test_intermediate_acteurs",
        bash_command=("dbt test --models intermediate.acteurs"),
    )

    dbt_run_marts_acteurs_exhaustive = BashOperator(
        task_id="dbt_run_marts_acteurs_exhaustive",
        bash_command=("dbt run --models marts.acteurs.exhaustive"),
    )
    dbt_test_marts_acteurs_exhaustive = BashOperator(
        task_id="dbt_test_marts_acteurs_exhaustive",
        bash_command=("dbt test --models marts.acteurs.exhaustive"),
    )
    dbt_run_exposure_acteurs_exhaustive = BashOperator(
        task_id="dbt_run_exposure_acteurs_exhaustive",
        bash_command=("dbt run --models exposure.acteurs.exhaustive"),
    )
    dbt_test_exposure_acteurs_exhaustive = BashOperator(
        task_id="dbt_test_exposure_acteurs_exhaustive",
        bash_command=("dbt test --models exposure.acteurs.exhaustive"),
    )

    dbt_run_marts_acteurs_carte = BashOperator(
        task_id="dbt_run_marts_acteurs_carte",
        bash_command=("dbt run --models marts.acteurs.carte"),
    )
    dbt_test_marts_acteurs_carte = BashOperator(
        task_id="dbt_test_marts_acteurs_carte",
        bash_command=("dbt test --models marts.acteurs.carte"),
    )
    dbt_run_exposure_acteurs_carte = BashOperator(
        task_id="dbt_run_exposure_acteurs_carte",
        bash_command=("dbt run --models exposure.acteurs.carte"),
    )
    dbt_test_exposure_acteurs_carte = BashOperator(
        task_id="dbt_test_exposure_acteurs_carte",
        bash_command=("dbt test --models exposure.acteurs.carte"),
    )

    dbt_run_marts_acteurs_opendata = BashOperator(
        task_id="dbt_run_marts_acteurs_opendata",
        bash_command=("dbt run --models marts.acteurs.opendata"),
    )
    dbt_test_marts_acteurs_opendata = BashOperator(
        task_id="dbt_test_marts_acteurs_opendata",
        bash_command=("dbt test --models marts.acteurs.opendata"),
    )
    dbt_run_exposure_acteurs_opendata = BashOperator(
        task_id="dbt_run_exposure_acteurs_opendata",
        bash_command=("dbt run --models exposure.acteurs.opendata"),
    )
    dbt_test_exposure_acteurs_opendata = BashOperator(
        task_id="dbt_test_exposure_acteurs_opendata",
        bash_command=("dbt test --models exposure.acteurs.opendata"),
    )

    check_model_table_displayedacteur_task = check_model_table_consistency_task(
        dag, "DisplayedActeur", "exposure_carte_acteur"
    )
    check_model_table_displayedpropositionservice_task = (
        check_model_table_consistency_task(
            dag, "DisplayedPropositionService", "exposure_carte_propositionservice"
        )
    )
    # The publication isn't handled by DBT yet
    # replace_displayedacteur_table_task = replace_acteur_table_task(
    #     dag, "qfdmo_displayed", "exposure_carte_"
    # )

    check_model_table_vueacteur_task = check_model_table_consistency_task(
        dag, "VueActeur", "exposure_exhaustive_acteur"
    )
    check_model_table_vuepropositionservice_task = check_model_table_consistency_task(
        dag, "VuePropositionService", "exposure_exhaustive_propositionservice"
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
        >> dbt_run_marts_acteurs_exhaustive
        >> dbt_test_marts_acteurs_exhaustive
        >> dbt_run_exposure_acteurs_exhaustive
        >> dbt_test_exposure_acteurs_exhaustive
        >> dbt_run_marts_acteurs_carte
        >> dbt_test_marts_acteurs_carte
        >> dbt_run_exposure_acteurs_carte
        >> dbt_test_exposure_acteurs_carte
        >> dbt_run_marts_acteurs_opendata
        >> dbt_test_marts_acteurs_opendata
        >> dbt_run_exposure_acteurs_opendata
        >> dbt_test_exposure_acteurs_opendata
    )

    # Définir la séquence de vérification en parallèle
    (
        dbt_test_exposure_acteurs_carte
        >> check_model_table_displayedacteur_task
        >> check_model_table_displayedpropositionservice_task
        # >> replace_displayedacteur_table_task
    )

    (
        dbt_test_exposure_acteurs_exhaustive
        >> check_model_table_vueacteur_task
        >> check_model_table_vuepropositionservice_task
        >> replace_vueacteur_table_task
    )
