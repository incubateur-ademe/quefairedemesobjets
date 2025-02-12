import logging

import numpy as np
import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.airflow_logic.task_ids import (
    TASK_CLUSTERS_DISPLAY,
    TASK_CONFIG_CREATE,
    TASK_NORMALIZE,
)
from cluster.tasks.business_logic.cluster_acteurs_add_original_df_columns import (
    cluster_acteurs_add_original_df_columns,
)
from cluster.tasks.business_logic.cluster_acteurs_clusters import (
    cluster_acteurs_clusters,
)
from cluster.tasks.business_logic.cluster_acteurs_df_sort import cluster_acteurs_df_sort
from cluster.tasks.business_logic.cluster_acteurs_selection_children import (
    cluster_acteurs_selection_children,
)
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()


logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_CLUSTERS_DISPLAY}"
    ============================================================

    💡 quoi: génère des suggestions de clusters pour les acteurs

    🎯 pourquoi: c'est le but de ce DAG :)

    🏗️ comment: les suggestions sont générées après la normalisation
    avec les paramètres cluster_ du DAG
    """


def cluster_acteurs_suggestions_wrapper(**kwargs) -> None:

    from data.models.change import (
        COL_ENTITY_TYPE,
        ENTITY_ACTEUR_DISPLAYED,
        ENTITY_ACTEUR_REVISION,
    )
    from qfdmo.models import RevisionActeur

    logger.info(task_info_get())

    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids=TASK_CONFIG_CREATE
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(key="df", task_ids=TASK_NORMALIZE)
    if df.empty:
        raise ValueError("Pas de données acteurs normalisées récupérées")

    log.preview("config reçue", config)
    # Zoom sur les champs de config de clustering pour + de clarté
    for key, value in config.__dict__.items():
        if key.startswith("cluster_"):
            log.preview(f"config.{key}", value)
    log.preview("acteurs normalisés", df)

    df_clusters = cluster_acteurs_clusters(
        df,
        cluster_fields_exact=config.cluster_fields_exact,
        cluster_fields_fuzzy=config.cluster_fields_fuzzy,
        cluster_fields_separate=config.cluster_fields_separate,
        cluster_fuzzy_threshold=config.cluster_fuzzy_threshold,
    )
    if df_clusters.empty:
        raise AirflowSkipException(log.banner_string("Pas de clusters trouvés -> stop"))
    log.preview_df_as_markdown("Clusters orphelins+parents", df_clusters)

    logger.info("Ajout des colonnes de la df d'origine (ignorées par le clustering)")
    df_clusters = cluster_acteurs_add_original_df_columns(df_clusters, df)
    df_clusters[COL_ENTITY_TYPE] = ENTITY_ACTEUR_DISPLAYED

    logger.info("Ajout des données calculées")
    # TODO: créer une fonction dédiée qui permet de consolider:
    # - la df de suggestions (données uniquement nécessaires aux clusters)
    # - la df de sélection (données complètes des acteurs)
    # pour pouvoir offrire en sortie de suggestion une df complète
    # qui permettre + de validation/suivis au delà de ce qui est
    # nécessaire pour le clustering lui-même
    # En attendant un quick-fix pour récupérer le statut et passer la validation
    # status_by_id = df.set_index("identifiant_unique")["statut"]
    # df_clusters["statut"] = df_clusters["identifiant_unique"].map(status_by_id)

    # Parent ID n'est pas présent dans DisplayedActeur (source des clusters)
    # donc on reconstruit ce champ à partir de RevisionActeur
    parent_ids_by_id = dict(
        RevisionActeur.objects.filter(parent__isnull=False).values_list(
            "identifiant_unique", "parent__identifiant_unique"
        )
    )
    df_clusters["parent_id"] = df_clusters["identifiant_unique"].map(
        lambda x: parent_ids_by_id.get(x, None)
    )

    logger.info("Ajout des enfants des parents existants")
    df_parents = df_clusters[df_clusters["nombre_enfants"] > 0]
    parent_to_cluster_ids = df_parents.set_index("identifiant_unique")[
        "cluster_id"
    ].to_dict()
    parent_ids = df_parents["identifiant_unique"].tolist()
    log.preview("parent_ids", parent_ids)
    df_children = cluster_acteurs_selection_children(
        parent_ids=parent_ids,
        fields_to_include=config.fields_protected
        + config.fields_transformed
        + ["parent_id"],
    )
    df_children["cluster_id"] = df_children["parent_id"].map(parent_to_cluster_ids)
    df_children[COL_ENTITY_TYPE] = ENTITY_ACTEUR_REVISION

    log.preview_df_as_markdown("enfants des parents", df_children)

    df_all = pd.concat([df_clusters, df_children], ignore_index=True).replace(
        {np.nan: None}
    )

    df_all = cluster_acteurs_df_sort(
        df_all,
        cluster_fields_exact=config.cluster_fields_exact,
        cluster_fields_fuzzy=config.cluster_fields_fuzzy,
    )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("suggestions de clusters", df_all, groupby="cluster_id")

    # On pousse les suggestions dans xcom pour les tâches suivantes
    kwargs["ti"].xcom_push(key="df", value=df_all)


def cluster_acteurs_clusters_display_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_CLUSTERS_DISPLAY,
        python_callable=cluster_acteurs_suggestions_wrapper,
        provide_context=True,
        dag=dag,
    )
