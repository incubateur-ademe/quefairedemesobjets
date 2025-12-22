import logging

import numpy as np
import pandas as pd
from airflow.exceptions import AirflowFailException
from cluster.tasks.business_logic.cluster_acteurs_clusters import (
    cluster_acteurs_clusters,
)
from cluster.tasks.business_logic.cluster_acteurs_read.children import (
    cluster_acteurs_read_children,
)
from cluster.tasks.business_logic.misc.df_sort import df_sort
from utils import logging_utils as log
from utils.dataframes import df_add_original_columns

logger = logging.getLogger(__name__)


def cluster_acteurs_clusters_prepare(
    df: pd.DataFrame,
    cluster_fields_exact: list[str],
    cluster_fields_fuzzy: list[str],
    cluster_fuzzy_threshold: float,
    cluster_intra_source_is_allowed: bool,
    fields_protected: list[str],
    fields_transformed: list[str],
    include_source_ids: list[int],
) -> pd.DataFrame:
    """Overall clustering preparation:
    - Clustering of actors
    - Adding original columns
    - Adding calculated columns
    - Adding children of parents
    - Sorting the final dataframe"""

    from qfdmo.models import RevisionActeur

    def filter_clusters_without_any_included_sources(
        df_clusters: pd.DataFrame, include_source_ids: list[int]
    ) -> pd.DataFrame:
        """
        remove cluster if none of the acteur belongs one of the sources to include
        """
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

    df_clusters = cluster_acteurs_clusters(
        df,
        cluster_fields_exact=cluster_fields_exact,
        cluster_fields_fuzzy=cluster_fields_fuzzy,
        cluster_fuzzy_threshold=cluster_fuzzy_threshold,
        cluster_intra_source_is_allowed=cluster_intra_source_is_allowed,
    )
    log.preview_df_as_markdown("Clusters orphelins+parents", df_clusters)
    if df_clusters.empty:
        logger.info("Pas de clusters trouvés, on arrête là")
        return df_clusters

    logger.info("Ajout des colonnes de la df d'origine (ignorées par le clustering)")
    df_clusters = df_add_original_columns(df_clusters, df)

    logger.info("Ajout des données calculées")

    # TODO: remove this entire logic by using a unified django model
    # abstracting/resolving the location/computation of acteurs
    # and thus not needing any of this
    acteur_to_parent_ids_all = dict(
        RevisionActeur.objects.filter(parent__isnull=False).values_list(
            "identifiant_unique", "parent__identifiant_unique"
        )
    )
    df_clusters["parent_id"] = df_clusters["identifiant_unique"].map(
        lambda x: acteur_to_parent_ids_all.get(x, None)
    )

    # Ensure nombre_enfants is an integer and not NaN
    df_clusters["nombre_enfants"] = df_clusters["nombre_enfants"].fillna(0)
    df_clusters["nombre_enfants"] = df_clusters["nombre_enfants"].astype(int)

    # Case with no parents (no existing parents found or clustered)
    df_parents = df_clusters[df_clusters["nombre_enfants"] > 0]
    logger.info(f"# parents trouvés dans les clusters: {len(df_parents)}")
    if df_parents.empty:
        logger.info("Pas de parents dans clusters -> pas d'enfants à ajouter")
        df_combined = df_clusters
    else:

        # Case with parents
        logger.info("Ajout des enfants des parents existants")
        parent_to_cluster_ids = df_parents.set_index("identifiant_unique")[
            "cluster_id"
        ].to_dict()
        parent_ids = df_parents["identifiant_unique"].tolist()
        log.preview("parent_ids", parent_ids)
        df_children = cluster_acteurs_read_children(
            parent_ids=parent_ids,
            fields_to_include=fields_protected
            + fields_transformed
            + ["source_id", "parent_id"],
        )

        # Validation
        # we should either enter df_parents.empty or be here with children
        if df_children.empty:
            raise AirflowFailException(
                "Pas d'enfants trouvés pour les parents, ce qui ne devrait pas arriver"
            )
        df_children["cluster_id"] = df_children["parent_id"].map(parent_to_cluster_ids)
        df_combined = pd.concat([df_clusters, df_children], ignore_index=True).replace(
            {np.nan: None}
        )

    df_combined = filter_clusters_without_any_included_sources(
        df_combined, include_source_ids
    )

    df_combined = df_sort(
        df_combined,
        cluster_fields_exact=cluster_fields_exact,
        cluster_fields_fuzzy=cluster_fields_fuzzy,
    )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown(
        "suggestions de clusters", df_combined, groupby="cluster_id"
    )

    return df_combined
