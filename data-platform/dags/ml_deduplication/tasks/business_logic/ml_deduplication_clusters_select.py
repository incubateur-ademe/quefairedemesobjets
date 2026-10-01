"""Select clusters from the inference output and enrich them.

After inference, two tables exist in the warehouse DB:
  - <output_table>_clusters  (entity_id, cluster_id, score_true, run_id)
  - <output_table>_predictions

This task reads the clusters for the current run_id, joins the full acteur
rows (by entity_id = identifiant_unique), then enriches the result exactly
like the clustering DAG's `clusters_prepare` step so the downstream
parent/suggestion logic can be reused as-is.
"""

import logging

import pandas as pd
from airflow.sdk.exceptions import AirflowFailException
from cluster.tasks.business_logic.misc.df_sort import df_sort
from ml_deduplication.config.models import MLDeduplicationConfig
from utils import logging_utils as log
from utils.django import (
    DJANGO_WH_CONNECTION_NAME,
    django_conn_to_sqlalchemy_engine,
    django_setup_full,
)

logger = logging.getLogger(__name__)


def _clusters_read(run_id: str, output_table: str) -> pd.DataFrame:
    """Read the inference clusters for a run_id from the warehouse DB."""
    engine = django_conn_to_sqlalchemy_engine(using=DJANGO_WH_CONNECTION_NAME)
    clusters_table = f"{output_table}_clusters"
    df = pd.read_sql(
        f"SELECT * FROM {clusters_table} WHERE run_id = %(run_id)s",
        engine,
        params={"run_id": run_id},
    ).replace({pd.NA: None})
    entities_count_by_cluster = df.groupby("cluster_id")["entity_id"].count()
    multi_entities_cluster = entities_count_by_cluster[entities_count_by_cluster > 1]

    df = df[df["cluster_id"].isin(multi_entities_cluster.index)]
    logger.info(f"# clusters lus pour {run_id=}: {len(df)}")
    return df


def _acteurs_read_for_entities(entities: list[str], fields: list[str]) -> pd.DataFrame:
    """Read full acteur rows (plus computed codes) for the given entities."""
    django_setup_full()
    from qfdmo.models import ActeurType, Source
    from qfdmo.models.acteur import VueActeur

    acteurs = VueActeur.objects.filter(identifiant_unique__in=entities)
    data = [{field: getattr(a, field) for field in fields} for a in acteurs]
    df = pd.DataFrame(data, dtype="object").replace({pd.NA: None})

    if df.empty:
        return df

    mapping_source_codes_by_ids = {x.id: x.code for x in Source.objects.all()}
    mapping_acteur_type_codes_by_ids = {x.id: x.code for x in ActeurType.objects.all()}
    df["source_code"] = df["source_id"].map(mapping_source_codes_by_ids)
    df["acteur_type_code"] = df["acteur_type_id"].map(mapping_acteur_type_codes_by_ids)
    df["source_codes"] = df["source_code"].apply(lambda x: [x] if x else [])
    return df


def filter_clusters_without_any_included_sources(
    df_clusters: pd.DataFrame, include_source_ids: list[int]
) -> pd.DataFrame:
    nb_clusters_before = len(df_clusters["cluster_id"].unique())
    rows_with_included_sources = df_clusters["source_id"].isin(include_source_ids)
    clusters_with_included_sources = (
        df_clusters.loc[rows_with_included_sources, "cluster_id"]
        .dropna()
        .unique()
        .tolist()
    )
    df_clusters = df_clusters[
        df_clusters["cluster_id"].isin(clusters_with_included_sources)
    ]
    nb_clusters_after = len(df_clusters["cluster_id"].unique())
    if nb_clusters_filtered := nb_clusters_before - nb_clusters_after:
        logger.warning(
            "Clusters supprimés car aucune source concernée: "
            f"{nb_clusters_filtered} / {nb_clusters_before}"
        )
    return df_clusters


def ml_deduplication_clusters_select(
    config: MLDeduplicationConfig,
    run_id: str,
) -> pd.DataFrame:
    """Read + enrich the clusters produced by the inference for a run.

    The result has the same shape as the clustering DAG's `clusters_prepare`
    output (cluster_id + full acteur columns + parent_id), so the reused
    parent/suggestion tasks work unchanged.
    """
    django_setup_full()

    df_clusters = _clusters_read(run_id=run_id, output_table=config.output_table)
    if df_clusters.empty:
        logger.info("Pas de clusters trouvés pour ce run, on s'arrête là")
        return df_clusters

    # Columns to read from VueActeur: everything except computed props
    # (source_code/acteur_type_code/source_codes handled separately).
    db_fields = [
        f
        for f in config.fields_all
        if f not in ["source_code", "acteur_type_code", "source_codes"]
    ]
    fields = list(
        dict.fromkeys(
            [
                "identifiant_unique",
                *db_fields,
                "source_id",
                # Computed prop (not a DB column) required by downstream
                # tasks (df_metadata_get in cluster_acteurs_suggestions_to_db).
                "nombre_enfants",
                "est_parent",
            ]
        )
    )

    entities = df_clusters["entity_id"].tolist()
    df_acteurs = _acteurs_read_for_entities(entities, fields)

    if df_acteurs.empty:
        raise AirflowFailException(
            "Clusters trouvés mais aucun acteur correspondant en base"
        )

    # Attach cluster_id to the acteurs
    entity_to_cluster = df_clusters.set_index("entity_id")["cluster_id"].to_dict()
    df = df_acteurs.copy()
    df["cluster_id"] = df["identifiant_unique"].map(entity_to_cluster)
    df = df.dropna(subset=["cluster_id"])

    log.preview_df_as_markdown("Clusters (acteurs + cluster_id)", df)

    # Add parent_id for every acteur (existing acteur -> parent mapping)
    from qfdmo.models import RevisionActeur

    acteur_to_parent_ids_all = dict(
        RevisionActeur.objects.filter(parent__isnull=False).values_list(
            "identifiant_unique", "parent__identifiant_unique"
        )
    )
    df["parent_id"] = df["identifiant_unique"].map(
        lambda x: acteur_to_parent_ids_all.get(x, None)
    )
    df_combined = filter_clusters_without_any_included_sources(
        df, config.include_source_ids
    )

    df_combined = df_sort(df_combined)

    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("clusters enrichis", df_combined, groupby="cluster_id")

    return df_combined
