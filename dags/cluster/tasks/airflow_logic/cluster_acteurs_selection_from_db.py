import logging

import numpy as np
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.business_logic import (
    cluster_acteurs_df_sort,
    cluster_acteurs_selection_acteur_type_parents,
    cluster_acteurs_selection_from_db,
)
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

from qfdmo.models import DisplayedActeur  # noqa: E402

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_selection_from_db"
    ============================================================

    💡 quoi: va chercher en base de données les acteurs correspondants
        aux critères d'inclusion et d'exclusion du DAG
         - ces acteurs "candidats" ne seront pas forcément utilisés
         dans des clusters

    🎯 pourquoi: c'est la donnée de base dont on a besoin pour le clustering

    🏗️ comment: constructions/execution d'une requête SQL sur la base
        des critrères d'inclusion/exclusion
    """


def cluster_acteurs_selection_from_db_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids="cluster_acteurs_config_create"
    )
    log.preview("Config reçue", config)

    # --------------------------------
    # 1) Sélection des acteurs
    # --------------------------------
    # Quels qu'ils soient (enfants ou parents) sur la
    # base de tous les critères d'inclusion/exclusion
    # fournis au niveau du DAG
    logging.info(log.banner_string("Sélection des acteurs"))
    df_acteurs, query = cluster_acteurs_selection_from_db(
        model_class=DisplayedActeur,
        include_source_ids=config.include_source_ids,
        include_acteur_type_ids=config.include_acteur_type_ids,
        include_only_if_regex_matches_nom=config.include_only_if_regex_matches_nom,
        include_if_all_fields_filled=config.include_if_all_fields_filled,
        exclude_if_any_field_filled=config.exclude_if_any_field_filled,
        extra_dataframe_fields=config.fields_used,
    )
    df_acteurs = cluster_acteurs_df_sort(df_acteurs)
    log.preview("requête SQL utilisée", query)
    log.preview("# acteurs par source_id", df_acteurs.groupby("source_id").size())
    log.preview(
        "# acteurs par acteur_type_id", df_acteurs.groupby("acteur_type_id").size()
    )
    log.preview_df_as_markdown("acteurs sélectionnés", df_acteurs)

    # --------------------------------
    # 2) Sélection des parents uniquements
    # --------------------------------
    # Aujourd'hui (2025-01-27): la convention data veut qu'un parent
    # soit attribué une source NULL. Donc si le métier choisit de
    # clusteriser des sources en particulier à 1), on ne peut donc
    # jamais récupérer les parents potentiels pour le même type d'acteur
    # La logique ci-dessous vient palier à ce problème en sélectionnant
    # TOUS les parents des acteurs types sélectionnés, et en ignorant
    # les autres paramètres de sélection
    logging.info(log.banner_string("Sélection des parents"))
    df_parents = cluster_acteurs_selection_acteur_type_parents(
        acteur_type_ids=config.include_acteur_type_ids,
        fields=config.fields_used,
    )
    df_parents = cluster_acteurs_df_sort(df_parents)
    log.preview_df_as_markdown("parents sélectionnés", df_parents)

    # --------------------------------
    # 3) Fusion acteurs + parents
    # --------------------------------
    logging.info(log.banner_string("Fusion acteurs + parents"))
    ids = set()
    ids.update(df_acteurs["identifiant_unique"].values)
    ids.update(df_parents["identifiant_unique"].values)
    log.preview("IDs avant la fusion", ids)
    df = pd.concat([df_acteurs, df_parents], ignore_index=True).replace({np.nan: None})
    df = df.drop_duplicates(subset="identifiant_unique", keep="first")
    df = cluster_acteurs_df_sort(df)
    log.preview("IDs après la fusion", df["identifiant_unique"].tolist())
    log.preview_df_as_markdown("acteurs + parents sélectionnés", df)

    if df.empty:
        raise ValueError("Aucun acteur trouvé avec les critères de sélection")

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    df = cluster_acteurs_df_sort(df)
    log.preview_df_as_markdown("acteurs sélectionnés", df)

    kwargs["ti"].xcom_push(key="df", value=df)


def cluster_acteurs_selection_from_db_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="cluster_acteurs_selection_from_db",
        python_callable=cluster_acteurs_selection_from_db_wrapper,
        dag=dag,
    )
