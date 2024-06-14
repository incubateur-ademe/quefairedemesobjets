from datetime import datetime
from importlib import import_module
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")
dag_eo_utils = import_module(f"{env}.utils.dag_eo_utils")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 23),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}

dag = DAG(
    utils.get_dag_name(__file__, "pyreo"),
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Pyreo dataset"
    ),
    schedule_interval=None,
)


fetch_data_task = PythonOperator(
    task_id="fetch_data_from_api",
    python_callable=dag_eo_utils.fetch_data_from_api,
    op_kwargs={"dataset": "donnees-eo-pyreo"},
    dag=dag,
)

load_data_task = PythonOperator(
    task_id="load_data_from_postgresql",
    python_callable=dag_eo_utils.load_data_from_postgresql,
    dag=dag,
)

create_actors_task = PythonOperator(
    task_id="create_actors",
    python_callable=dag_eo_utils.create_actors,
    op_kwargs={
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "uniquement_sur_rdv": "",
            "exclusivite_de_reprisereparation": "",
            "filiere": "",
            "public_accueilli": "",
            "produitsdechets_acceptes": "",
            "labels_etou_bonus": "",
            "reprise": "",
            "point_de_reparation": "",
            "ecoorganisme": "source_id",
            "adresse_format_ban": "adresse",
            "nom_de_lorganisme": "nom",
            "_updatedAt": "cree_le",
            "perimetre_dintervention": "",
            "longitudewgs84": "location",
            "latitudewgs84": "location",
        },
        "default_column_value": {
            "type_de_point_de_collecte": "magasin / franchise,"
            " enseigne commerciale / distributeur / point de vente"
        },
    },
    dag=dag,
)

create_proposition_services_task = PythonOperator(
    task_id="create_proposition_services",
    python_callable=dag_eo_utils.create_proposition_services,
    dag=dag,
)

create_proposition_services_sous_categories_task = PythonOperator(
    task_id="create_proposition_services_sous_categories",
    python_callable=dag_eo_utils.create_proposition_services_sous_categories,
    dag=dag,
)

write_data_task = PythonOperator(
    task_id="write_data_to_validate_into_dagruns",
    python_callable=dag_eo_utils.write_to_dagruns,
    dag=dag,
)

serialize_to_json_task = PythonOperator(
    task_id="serialize_actors_to_records",
    python_callable=dag_eo_utils.serialize_to_json,
    dag=dag,
)

create_labels_task = PythonOperator(
    task_id="create_labels",
    python_callable=dag_eo_utils.create_labels,
    dag=dag,
)

(
    [fetch_data_task, load_data_task]
    >> create_actors_task
    >> [create_proposition_services_task, create_labels_task]
    >> create_proposition_services_sous_categories_task
    >> serialize_to_json_task
    >> write_data_task
)
