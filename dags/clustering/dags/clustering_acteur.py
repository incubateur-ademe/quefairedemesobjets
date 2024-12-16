from typing import Dict, List

from airflow import DAG
from airflow.decorators import task
from airflow.models.param import Param
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.tasks.airflow_logic.operators import default_args
from sources.tasks.business_logic.read_mapping_from_postgres import (
    read_mapping_from_postgres,
)
from sqlalchemy import inspect
from utils import logging_utils as log

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
dropdown_sources = list(f"{k} (id {v})" for k, v in mapping_source_id_by_code.items())
dropdown_acteur_types = list(
    f"{k} (id {v})" for k, v in mapping_acteur_type_id_by_code.items()
)


# Récupérer les IDs des valeurs sélectionnées
def ids_from_dropdowns(
    mapping_id_by_code: Dict[str, int],
    dropdown_all: List[str],
    dropdown_selected: List[str],
) -> List[int]:
    """Récupère les IDs correspondants aux valeurs
    sélectionnées dans un dropdown."""
    ids = list(mapping_id_by_code.values())
    dropdown_indices = [dropdown_all.index(v) for v in dropdown_selected]
    return [ids[i] for i in dropdown_indices]


def table_columns_get(table_name: str) -> List[str]:
    """
    Récupère la liste des colonnes d'une table dans une base de données.
    """
    engine = PostgresConnectionManager().engine
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)  # type: ignore
    return [column["name"] for column in columns]


dropdown_acteur_columns = table_columns_get("qfdmo_revisionacteur")


with DAG(
    dag_id="clustering_acteur",
    dag_display_name="Clustering - Acteur",
    default_args=default_args,
    description=("Un DAG pour générer des suggestions de clustering pour les acteurs"),
    params={
        "sources": Param(
            [],
            type="array",
            examples=dropdown_sources,
            description="Sources à inclure dans le clustering",
        ),
        "acteur_types": Param(
            [],
            type="array",
            # La terminologie Airflow n'est pas très heureuse
            # mais "examples" est bien la façon de faire des dropdowns
            # voir https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html
            examples=dropdown_acteur_types,
            description="Types d'acteurs à inclure dans le clustering",
        ),
        "colonnes_match_fuzzy": Param(
            [],
            type="array",
            examples=dropdown_acteur_columns,
            description="Colonnes à utiliser pour le match fuzzy (algo ML)",
        ),
        "colonnes_match_exact": Param(
            [],
            type="array",
            examples=dropdown_acteur_columns,
            description="""Clusteriser les acteurs SI les valeurs
            de ces colonnes sont identiques""",
        ),
        "intra_source": Param(
            False,
            type="boolean",
            description="Clusteriser les acteurs au sein d'une même source",
        ),
        "similarity_threshold": Param(
            0.8,
            type="number",
            minimum=0,
            maximum=1,
            description="Seuil de similarité pour le clustering",
        ),
    },
    schedule=None,
) as dag:

    @task()
    def clustering_acteur_config_validate(**kwargs) -> None:
        """Valider les paramètres du DAG pour le clustering acteur."""
        params = kwargs["params"]

        source_ids = ids_from_dropdowns(
            mapping_id_by_code=mapping_source_id_by_code,
            dropdown_all=dropdown_sources,
            dropdown_selected=params["sources"],
        )
        acteur_type_ids = ids_from_dropdowns(
            mapping_id_by_code=mapping_acteur_type_id_by_code,
            dropdown_all=dropdown_acteur_types,
            dropdown_selected=params["acteur_types"],
        )
        log.preview("sources sélectionnées", params["sources"])
        log.preview("sources ids correspondant", source_ids)
        log.preview("acteur_types sélectionnés", params["acteur_types"])
        log.preview("acteur_types ids correspondant", acteur_type_ids)

        columns_match_fuzzy = set(params["colonnes_match_fuzzy"])
        columns_match_exact = set(params["colonnes_match_exact"])
        columns_dups = columns_match_fuzzy.intersection(columns_match_exact)
        log.preview("colonnes match fuzzy", columns_match_fuzzy)
        log.preview("colonnes match exact", columns_match_exact)
        if columns_dups:
            raise ValueError(f"Colonnes {columns_dups} présentes dans fuzzy et exact")
        if not columns_match_fuzzy and not columns_match_exact:
            raise ValueError("Aucune colonne sélectionnée pour le clustering")

        intra_source = params["intra_source"]
        log.preview("intra_source", intra_source)
        if len(source_ids) == 1 and not intra_source:
            raise ValueError(f"1 source sélectionnée mais {intra_source=}")

    clustering_acteur_config_validate()
