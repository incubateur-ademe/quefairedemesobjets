import logging

import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.business_logic import (
    cluster_acteurs_clusters,
    cluster_acteurs_df_sort,
    cluster_acteurs_parent_calculations,
)
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

from qfdmo.models import RevisionActeur  # noqa: E402

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_clusters"
    ============================================================

    💡 quoi: génère des suggestions de clusters pour les acteurs

    🎯 pourquoi: c'est le but de ce DAG :)

    🏗️ comment: les suggestions sont générées après la normalisation
    avec les paramètres cluster_ du DAG
    """


def cluster_acteurs_suggestions_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids="cluster_acteurs_config_create"
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(
        key="df", task_ids="cluster_acteurs_normalize"
    )
    if df.empty:
        raise ValueError("Pas de données acteurs normalisées récupérées")

    log.preview("config reçue", config)
    log.preview("acteurs normalisés", df)

    df_clusters = cluster_acteurs_clusters(
        df,
        cluster_fields_exact=config.cluster_fields_exact,
        cluster_fields_fuzzy=config.cluster_fields_fuzzy,
        cluster_fields_separate=config.cluster_fields_separate,
        cluster_fuzzy_threshold=config.cluster_fuzzy_threshold,
    )
    if df_clusters.empty:
        raise AirflowSkipException(
            log.banner_string("Pas de suggestions de clusters générées")
        )

    logger.info("Ajout des données calculées")
    # TODO: créer une fonction dédiée qui permet de consolider:
    # - la df de suggestions (données uniquement nécessaires aux clusters)
    # - la df de sélection (données complètes des acteurs)
    # pour pouvoir offrire en sortie de suggestion une df complète
    # qui permettre + de validation/suivis au delà de ce qui est
    # nécessaire pour le clustering lui-même
    # En attendant un quick-fix pour récupérer le statut et passer la validation
    status_by_id = df.set_index("identifiant_unique")["statut"]
    df_clusters["statut"] = df_clusters["identifiant_unique"].map(status_by_id)

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

    df_clusters = cluster_acteurs_parent_calculations(df_clusters)

    df_clusters = cluster_acteurs_df_sort(
        df_clusters,
        cluster_fields_exact=config.cluster_fields_exact,
        cluster_fields_fuzzy=config.cluster_fields_fuzzy,
    )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("suggestions de clusters", df_clusters)

    # On pousse les suggestions dans xcom pour les tâches suivantes
    kwargs["ti"].xcom_push(key="df", value=df_clusters)


def cluster_acteurs_clusters_display_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="cluster_acteurs_clusters_display",
        python_callable=cluster_acteurs_suggestions_wrapper,
        provide_context=True,
        dag=dag,
    )
