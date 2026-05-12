"""
Fonctions de clustering des acteurs

TODO: améliorer le debug: en mode CLI on avant des logger.info()
qui étaient suffisants, mais en mode Airflow, on va faire
exploser la taille des logs, donc on a besoin de refactorer:
 - les fonctions doivent retourner des valeurs de debug
 - ces valeurs de debug vont être remontées à Airflow
 - dans airflow on pourra utiliser nos utilitaires genre log.preview()
    qui afficheront une partie du debug
"""

import logging
import re
from math import asin, cos, radians, sin, sqrt

import numpy as np
import pandas as pd
from cluster.tasks.business_logic.misc.cluster_exclude_intra_source import (
    split_clusters_infra_source,
)
from scipy.sparse import csr_matrix, triu
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from slugify import slugify
from unidecode import unidecode
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def cluster_id_from_strings(strings: list[str]) -> str:
    """
    Génère un cluster_id unique à partir de plusieurs strings

    Args:
        strings: liste de strings

    Returns:
        cluster_id
    """
    return "_".join(str(slugify(unidecode(str(x)))).lower() for x in strings)


def values_to_similarity_matrix_sparse(values: list[str]) -> csr_matrix:
    """Compute a sparse similarity matrix using TF-IDF vectorization."""
    vectorizer = TfidfVectorizer(
        tokenizer=str.split, binary=False, token_pattern=None  # type: ignore
    )  # type: ignore
    tfidf_matrix = vectorizer.fit_transform(values)
    return cosine_similarity(tfidf_matrix, dense_output=False).tocsr()


def score_normalize(score: np.float64, precision=5) -> int | float:
    """Convert a similarity score from numpy float either a 1 integer
    (if >=1 or 0) or a float"""
    # Convert value to Python int or float based on rules
    if score == 0:
        return 0
    if score >= 1:
        return 1
    return round(float(score), precision)


def sparse_similarity_matrix_to_clusters(
    similarity_matrix: csr_matrix,
    indexes: list[int],
    threshold: float,
) -> list[list[int]]:
    """Convert a sparse similarity matrix into clusters above a threshold."""
    if len(indexes) < 2:
        return []

    # With TF-IDF cosine similarity, scores are always in [0, 1].
    # threshold <= 0 therefore means a fully connected graph.
    if threshold <= 0:
        return [indexes]

    # keep half of the matrix (upper triangle)
    similarity_upper = triu(similarity_matrix, k=1, format="csr")
    # keep only the non-zero values
    rows, cols = similarity_upper.nonzero()
    # normalize the scores to be in [0, 1]
    normalized_scores = np.where(
        similarity_upper.data >= 1,
        1.0,
        np.round(similarity_upper.data.astype(float), 5),
    )
    # create a mask to keep only the values >= threshold as boolean
    mask = normalized_scores >= threshold
    if not mask.any():
        return []

    # keep only the values >= threshold for rows and cols and scores
    rows = rows[mask]
    cols = cols[mask]
    scores = normalized_scores[mask]

    # create matrix with only the rows and cols with values >= threshold
    adjacency = csr_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, cols)),
        shape=similarity_upper.shape,
    )
    adjacency = adjacency + adjacency.T

    # find connected components, create the clusters,
    # if A is linked to B
    # and if A is linked to C
    # then A, B and C are in the same cluster
    _, labels = connected_components(adjacency, directed=False, return_labels=True)

    # convert the labels to indexes
    clusters_by_label: dict[int, list[int]] = {}
    for local_index, label in enumerate(labels):
        clusters_by_label.setdefault(int(label), []).append(indexes[local_index])

    component_order: list[int] = []
    labels_seen: set[int] = set()
    for edge_index in np.argsort(-scores, kind="stable"):
        label = int(labels[rows[edge_index]])
        if label not in labels_seen:
            labels_seen.add(label)
            component_order.append(label)

    return [
        clusters_by_label[label]
        for label in component_order
        if len(clusters_by_label[label]) > 1
    ]


def cluster_to_subclusters(
    df: pd.DataFrame,
    column: str,
    cluster: list[int],
    threshold: float,
) -> list[list[int]]:
    """Split 1 cluster into subclusters based on a column matching threshold"""
    df_cluster = df.loc[cluster]
    column_values = df_cluster[column].astype(str).values
    similarity_matrix = values_to_similarity_matrix_sparse(column_values.tolist())
    return sparse_similarity_matrix_to_clusters(similarity_matrix, cluster, threshold)


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate great circle distance between two points on earth (in decimal degrees).
    Returns distance in meters."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return c * 6371000  # Earth radius in meters


def split_clusters_by_distance(
    df_src: pd.DataFrame, distance_threshold: int
) -> list[pd.Series | pd.DataFrame]:
    """Split a cluster into distance-based subclusters.

    Work like `cluster_cols_group_fuzzy`: take a DataFrame representing
    *one* original cluster, and return a list of Series or DataFrames representing
    subclusters.
    """

    # We only consider clusters of size 2+
    if len(df_src) < 2:
        return []

    # In no coordinates -> no split: keep the original cluster as is
    if "latitude" not in df_src.columns or "longitude" not in df_src.columns:
        raise ValueError(
            "Can't split cluster by distance: no latitude or longitude columns found"
        )

    # Remove rows with missing coordinates (cannot be connected to anything)
    df_src = df_src.dropna(subset=["latitude", "longitude"])
    if len(df_src) < 2:
        return []

    indices = list(df_src.index)
    n = len(indices)

    # Build adjacency graph based on distance
    adjacency: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        lat1, lon1 = (
            df_src.loc[indices[i], "latitude"],
            df_src.loc[indices[i], "longitude"],
        )
        for j in range(i + 1, n):
            lat2, lon2 = (
                df_src.loc[indices[j], "latitude"],
                df_src.loc[indices[j], "longitude"],
            )
            dist = haversine(lon1, lat1, lon2, lat2)
            if dist < distance_threshold:
                adjacency[i].append(j)
                adjacency[j].append(i)

    # Find connected components using iterative DFS
    visited = [False] * n
    components: list[list[int]] = []
    for i in range(n):
        if visited[i]:
            continue
        component: list[int] = []
        stack = [i]
        while stack:
            node = stack.pop()
            if visited[node]:
                continue
            visited[node] = True
            component.append(node)
            for neighbor in adjacency[node]:
                if not visited[neighbor]:
                    stack.append(neighbor)
        if len(component) >= 2:
            components.append(component)

    return [
        df_src.loc[[indices[idx] for idx in component]].reset_index(drop=True)
        for component in components
    ]


def cluster_cols_group_fuzzy(
    df_src: pd.DataFrame, columns_fuzzy: list[str], threshold: float
) -> list[pd.DataFrame]:
    """Apply fuzzy clustering to split a df into subclusters"""

    # Initialize with all rows as a single cluster
    df = df_src.copy()
    for column in columns_fuzzy:
        # Remove rows with None or empty string values
        df = df.dropna(subset=[column])
        df = df[df[column].astype(str).str.strip() != ""]

    # On ne considère que les clusters de taille 2+
    if len(df) < 2:
        return []

    clusters = [list(df.index)]

    for column in columns_fuzzy:
        clusters_ref = []
        for cluster in clusters:
            clusters_ref_new = cluster_to_subclusters(df, column, cluster, threshold)
            clusters_ref.extend(clusters_ref_new)

        # Only continue with valid clusters for the next refinement step
        clusters = [cluster for cluster in clusters_ref if len(cluster) > 1]

    # Convert clusters into DataFrames
    result_dfs = [df.loc[cluster].reset_index(drop=True) for cluster in clusters]

    return result_dfs


def _groups_with_revalidation_keys(
    keys: list[str], subclusters: list[pd.DataFrame], step_name: str
) -> list[tuple[list[str], pd.DataFrame]]:
    """Keep the original keys when a split keeps a single cluster.

    If the split creates several valid subclusters, append a suffix to keep
    generated cluster ids unique.
    """

    if not subclusters:
        return []
    if len(subclusters) == 1:
        return [(keys, subclusters[0])]
    return [
        (keys + [step_name, str(i + 1)], rows) for i, rows in enumerate(subclusters)
    ]


def revalidate_groups_after_intra_source_split(
    groups: list[tuple[list[str], pd.DataFrame]],
    cluster_fields_fuzzy: list[str],
    cluster_fuzzy_threshold: float,
    distance_in_cluster: int,
) -> list[tuple[list[str], pd.DataFrame]]:
    """Re-apply clustering constraints after intra-source splitting.

    The intra-source split is source-based only and can create subsets that no
    longer satisfy the original fuzzy or distance constraints.
    """

    if not cluster_fields_fuzzy and distance_in_cluster <= 0:
        return groups

    revalidated_groups = []
    for keys, rows in groups:
        groups_after_fuzzy = [(keys, rows)]
        if cluster_fields_fuzzy:
            subclusters_fuzzy = cluster_cols_group_fuzzy(
                df_src=rows,
                columns_fuzzy=cluster_fields_fuzzy,
                threshold=cluster_fuzzy_threshold,
            )
            groups_after_fuzzy = _groups_with_revalidation_keys(
                keys, subclusters_fuzzy, "fuzzy_recheck"
            )

        groups_after_distance = groups_after_fuzzy
        if distance_in_cluster > 0:
            groups_after_distance = []
            for fuzzy_keys, fuzzy_rows in groups_after_fuzzy:
                subclusters_distance = split_clusters_by_distance(
                    df_src=fuzzy_rows,
                    distance_threshold=distance_in_cluster,
                )
                groups_after_distance.extend(
                    _groups_with_revalidation_keys(
                        fuzzy_keys, subclusters_distance, "distance_recheck"
                    )
                )

        revalidated_groups.extend(groups_after_distance)

    return revalidated_groups


def cluster_acteurs_clusters(
    df: pd.DataFrame,
    cluster_fields_exact: list[str] = [],
    cluster_fields_fuzzy: list[str] = [],
    cluster_fuzzy_threshold: float = 0.5,
    cluster_intra_source_is_allowed: bool = False,
    distance_in_cluster: int = 0,
) -> pd.DataFrame:
    """Core clustering logic (_prepare and _validate being additional
    logic such as combining clusters with their original data)"""

    # Validation
    for col in cluster_fields_exact:
        if col not in df.columns:
            raise ValueError(f"Colonne match exacte '{col}' pas dans le DataFrame")
    for col in cluster_fields_fuzzy:
        if col not in df.columns:
            raise ValueError(f"Colonne match fuzzy '{col}' pas dans le DataFrame")

    # DO NOT apply on potentially empty fields such as source_id (empty on parents)
    df = df.dropna(subset=cluster_fields_exact + cluster_fields_fuzzy)
    df = df.sort_values(cluster_fields_exact)

    # Only keep columns needed for clustering
    # TODO: replace re.search with fields coming from config
    cols_ids_codes = [
        col
        for col in df.columns
        if re.search(r"(^id|^identifiant|_code$|_id$)", col, re.I)
    ]
    cols_to_keep = list(
        set(
            cols_ids_codes
            + cluster_fields_exact
            + cluster_fields_fuzzy
            + ["source_codes"]
        )
    )
    if distance_in_cluster > 0:
        cols_to_keep.extend(["latitude", "longitude"])
    df = df[cols_to_keep]

    # Start with exact clustering with a simple groupby
    groups_after_exact_match: list[tuple[list[str], pd.DataFrame]] = []
    if cluster_fields_exact:
        for exact_keys, exact_rows in df.groupby(cluster_fields_exact):
            logger.info("\n\n")

            # Keep only clusters of size 2+
            if len(exact_rows) < 2:
                logger.info(f"🔴 Ignoré: cluster de taille <2: {list(exact_keys)}")
                continue

            keys = list(exact_keys)
            log.preview_df_as_markdown("🔵 Cluster potentiel exact", exact_rows)
            groups_after_exact_match.append((keys, exact_rows))
    else:
        groups_after_exact_match = [([], df)]

    logger.warning(f"groups_after_exact_match length: {len(groups_after_exact_match)}")

    groups_after_fuzzy_match = []
    if cluster_fields_fuzzy:
        for keys, exact_rows in groups_after_exact_match:
            keys_fuzzy = keys + cluster_fields_fuzzy
            subclusters = cluster_cols_group_fuzzy(
                df_src=exact_rows,
                columns_fuzzy=cluster_fields_fuzzy,
                threshold=cluster_fuzzy_threshold,
            )
            cnt = len(subclusters)
            status = "🔵" if cnt else "🔴"
            logger.info(f"{status} Après fuzzy: #{cnt} sous-clusters")
            for i, fuzzy_rows in enumerate(subclusters):
                fuzzy_keys = keys_fuzzy + [str(i + 1)]
                groups_after_fuzzy_match.append((fuzzy_keys, fuzzy_rows))
    else:
        groups_after_fuzzy_match = groups_after_exact_match

    logger.warning(f"groups_after_fuzzy_match length: {len(groups_after_fuzzy_match)}")

    groups_after_distance_match = []
    if distance_in_cluster > 0:
        for keys, fuzzy_rows in groups_after_fuzzy_match:
            keys_distance = keys + ["distance"]
            subclusters = split_clusters_by_distance(
                df_src=fuzzy_rows,
                distance_threshold=distance_in_cluster,
            )
            cnt = len(subclusters)
            status = "🔵" if cnt else "🔴"
            logger.info(f"{status} Après distance: #{cnt} sous-clusters")
            logger.warning(subclusters)
            for i, distance_rows in enumerate(subclusters):
                distance_keys = keys_distance + [str(i + 1)]
                groups_after_distance_match.append((distance_keys, distance_rows))
    else:
        groups_after_distance_match = groups_after_fuzzy_match

    logger.warning(
        f"groups_after_distance_match length: {len(groups_after_distance_match)}"
    )

    if not cluster_intra_source_is_allowed:
        groups_after_distance_match = split_clusters_infra_source(
            groups_after_distance_match
        )
        groups_after_distance_match = revalidate_groups_after_intra_source_split(
            groups=groups_after_distance_match,
            cluster_fields_fuzzy=cluster_fields_fuzzy,
            cluster_fuzzy_threshold=cluster_fuzzy_threshold,
            distance_in_cluster=distance_in_cluster,
        )

    logger.warning(
        "groups_after_distance_match length after intrasource split: "
        f"{len(groups_after_distance_match)}"
    )

    # For all potential clusters, we apply the intra-source logic
    clusters = []
    for keys_final, rows in groups_after_distance_match:
        cluster_id = cluster_id_from_strings(keys_final)
        rows["cluster_id"] = cluster_id
        clusters.append(rows.copy())

    if not clusters:
        return pd.DataFrame()

    # Combining all cluster
    df_clusters = pd.concat(clusters)

    # Extra safety to only keep 2+
    df_clusters = df_clusters.groupby("cluster_id").filter(lambda x: len(x) >= 2)

    # Info
    logger.info(f"🟢 {df_clusters['cluster_id'].nunique()=}")
    logger.info(f"🟢 {df_clusters['identifiant_unique'].nunique()=}")

    return df_clusters
