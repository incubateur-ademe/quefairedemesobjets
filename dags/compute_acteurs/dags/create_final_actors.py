from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.airflow_logic import (
    apply_corrections_acteur_task,
    compute_parent_ps_task,
    compute_ps_task,
    db_data_write_task,
    deduplicate_acteur_serivces_task,
    deduplicate_acteur_sources_task,
    deduplicate_labels_task,
    merge_acteur_services_task,
    merge_labels_task,
)
from utils.db_tasks import read_data_from_postgres

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 7),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Retry settings for reading tasks
read_retry_count = 5
read_retry_interval = timedelta(minutes=2)

dag = DAG(
    dag_id="compute_carte_acteur",
    dag_display_name="Rafraîchir les acteurs affichés sur la carte",
    default_args=default_args,
    description=(
        "Ce DAG récupère les données des acteurs et des propositions de services et"
        " applique les corrections. De plus, il déduplique les acteurs déclarés par"
        " plusieurs sources en cumulant leur services, sources et propositions"
        " services."
    ),
    schedule=None,
)

load_acteur_task = PythonOperator(
    task_id="load_acteur",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_propositionservice_task = PythonOperator(
    task_id="load_propositionservice",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_propositionservice"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_revisionacteur_task = PythonOperator(
    task_id="load_revisionacteur",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionacteur"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_revisionpropositionservice_task = PythonOperator(
    task_id="load_revisionpropositionservice",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionpropositionservice"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_revisionpropositionservice_sous_categories_task = PythonOperator(
    task_id="load_revisionpropositionservice_sous_categories",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionpropositionservice_sous_categories"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_propositionservice_sous_categories_task = PythonOperator(
    task_id="load_propositionservice_sous_categories",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_propositionservice_sous_categories"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_acteur_labels_task = PythonOperator(
    task_id="load_acteur_labels",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur_labels"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_acteur_acteur_services_task = PythonOperator(
    task_id="load_acteur_acteur_services",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur_acteur_services"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_revisionacteur_labels_task = PythonOperator(
    task_id="load_revisionacteur_labels",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionacteur_labels"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_revisionacteur_acteur_services_task = PythonOperator(
    task_id="load_revisionacteur_acteur_services",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionacteur_acteur_services"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)


apply_corrections_acteur_task_instance = apply_corrections_acteur_task(dag)
compute_ps_task_instance = compute_ps_task(dag)
compute_parent_ps_task_instance = compute_parent_ps_task(dag)
deduplicate_acteur_serivces_task_instance = deduplicate_acteur_serivces_task(dag)
deduplicate_acteur_sources_task_instance = deduplicate_acteur_sources_task(dag)
deduplicate_labels_task_instance = deduplicate_labels_task(dag)
merge_acteur_services_task_instance = merge_acteur_services_task(dag)
merge_labels_task_instance = merge_labels_task(dag)
db_data_write_task_instance = db_data_write_task(dag)


load_acteur_task >> apply_corrections_acteur_task_instance
[
    load_propositionservice_task,
    load_revisionpropositionservice_task,
    load_propositionservice_sous_categories_task,
    load_revisionpropositionservice_sous_categories_task,
] >> compute_ps_task_instance
[
    load_revisionacteur_task,
    load_acteur_labels_task,
    load_revisionacteur_labels_task,
] >> merge_labels_task_instance
[
    load_revisionacteur_task,
    load_acteur_acteur_services_task,
    load_revisionacteur_acteur_services_task,
] >> merge_acteur_services_task_instance
apply_corrections_acteur_task_instance >> compute_parent_ps_task_instance
apply_corrections_acteur_task_instance >> deduplicate_acteur_sources_task_instance
(compute_ps_task_instance >> compute_parent_ps_task_instance)
(
    merge_labels_task_instance
    >> apply_corrections_acteur_task_instance
    >> deduplicate_labels_task_instance
)
(
    merge_acteur_services_task_instance
    >> apply_corrections_acteur_task_instance
    >> deduplicate_acteur_serivces_task_instance
)
deduplicate_acteur_sources_task_instance >> db_data_write_task_instance
compute_parent_ps_task_instance >> db_data_write_task_instance
deduplicate_labels_task_instance >> db_data_write_task_instance
deduplicate_acteur_serivces_task_instance >> db_data_write_task_instance
