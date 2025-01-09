from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from clustering.tasks.airflow_logic.clustering_config_validate_task import (
    clustering_acteur_config_validate_task,
)
from clustering.tasks.airflow_logic.clustering_db_data_read_acteurs_task import (
    clustering_db_data_read_acteurs_task,
)
from sources.tasks.airflow_logic.operators import default_args
from sources.tasks.business_logic.read_mapping_from_postgres import (
    read_mapping_from_postgres,
)
from utils.airflow_params import airflow_params_dropdown_from_mapping

# On doit initialiser Django avant de pouvoir importer les modèles
from utils.django import django_model_fields_attributes_get, django_setup_full

# Obligé d'avoir la fonction setup avant l'import des modèles
django_setup_full()
from qfdmo.models import Acteur  # noqa: E402

default_args["retries"] = 0

# -------------------------------------------
# Gestion des dropdowns des paramètres
# -------------------------------------------
# A noter que ce design pattern est a éviter au maximum
# car le code est executé au parsing des fichiers DAG
# selon min_file_process_interval
# https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html#config-scheduler-min-file-process-interval
# https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#top-level-python-code
# En revanche sans cette approche, il va falloir:
# - soit laisser le métier rentrer des paramètres complexes à la main
# - soit maintenir des mapping statiques ici
# Ces deux options semblent pires que l'inconvénient du top-level code
# sachant que le code executé demeure assez légé

# Récupération données DB
mapping_source_id_by_code = read_mapping_from_postgres(table_name="qfdmo_source")
mapping_acteur_type_id_by_code = read_mapping_from_postgres(
    table_name="qfdmo_acteurtype"
)
# Création des dropdowns
dropdown_sources = airflow_params_dropdown_from_mapping(mapping_source_id_by_code)
dropdown_acteur_types = airflow_params_dropdown_from_mapping(
    mapping_acteur_type_id_by_code
)

dropdown_acteur_columns = django_model_fields_attributes_get(Acteur)

with DAG(
    dag_id="clustering_acteur",
    dag_display_name="Clustering - Acteur",
    default_args=default_args,
    description=("Un DAG pour générer des suggestions de clustering pour les acteurs"),
    params={
        "include_source_codes": Param(
            [],
            type="array",
            # La terminologie Airflow n'est pas très heureuse
            # mais "examples" est bien la façon de faire des dropdowns
            # voir https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html
            examples=dropdown_sources,
            description_md="""**➕ INCLUSION ACTEURS**: seuls ceux qui proviennent
            de ces sources
            (opérateur **OU/OR**)""",
        ),
        "include_acteur_type_codes": Param(
            [],
            type="array",
            examples=dropdown_acteur_types,
            description_md="""**➕ INCLUSION ACTEURS**: ceux qui sont de ces types
             (opérateur **OU/OR**)""",
        ),
        "include_if_all_fields_filled": Param(
            ["code_postal"],
            type="array",
            examples=dropdown_acteur_columns,
            description_md="""**➕ INCLUSION ACTEURS**: ceux dont tous ces champs
            sont **remplis**
             exemple: travailler uniquement sur les acteurs avec SIRET
             (opérateur **ET/AND**)""",
        ),
        "exclude_if_any_field_filled": Param(
            [],
            type=["null", "array"],
            examples=dropdown_acteur_columns,
            description_md="""**🛑 EXCLUSION ACTEURS**: ceux dont n'importe quel
            de ces champs est **rempli**
            exemple: travailler uniquement sur les acteurs SANS SIRET
            (opérateur **OU/OR**)""",
        ),
    },
    schedule=None,
) as dag:
    chain(
        clustering_acteur_config_validate_task(dag=dag),
        clustering_db_data_read_acteurs_task(dag=dag),
    )
