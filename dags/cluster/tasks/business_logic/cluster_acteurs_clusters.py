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

import numpy as np
import pandas as pd
from cluster.config.constants import COL_INDEX_SRC
from cluster.tasks.business_logic.misc.cluster_exclude_intra_source import (
    cluster_exclude_intra_source,
)
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


def cluster_strings(
    strings: list[str], threshold: float = 0.5
) -> list[tuple[list[int], list[str]]]:
    """Groupe des chaînes de caractères similaires en clusters
    sur la base de l'algo TF IDF

    Les clusters de 1 sont ignorés

    Args:
        strings: liste de chaînes de caractères
        threshold: seuil de similarité pour grouper les chaînes

    Returns:
        liste de clusters sous forme de tuples (indices, strings)
    """
    vectorizer = TfidfVectorizer(
        tokenizer=str.split, binary=False, token_pattern=None  # type: ignore
    )
    tfidf_matrix = vectorizer.fit_transform(strings)

    # Compute pairwise cosine similarity between strings
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # Sort pairs by similarity score in descending order
    indices = np.triu_indices_from(similarity_matrix, k=1)
    tuples = [
        (i, j, similarity_matrix[i, j])
        for i, j in zip(*indices)
        if similarity_matrix[i, j] >= threshold
    ]
    tuples.sort(key=lambda x: x[2], reverse=True)  # type: ignore

    visited = set()
    clusters = []

    for i, j, _ in tuples:
        if i not in visited and j not in visited:
            cluster = np.where(similarity_matrix[i] >= threshold)[0]
            cluster = [int(idx) for idx in cluster if idx not in visited]
            if cluster:
                visited.update(cluster)
                clusters.append((cluster, [strings[k] for k in cluster]))

    return clusters


def values_to_similarity_matrix(values: list[str]) -> np.ndarray:
    """Compute similarity matrix using TF-IDF vectorization
    on a list of values."""
    vectorizer = TfidfVectorizer(
        tokenizer=str.split, binary=False, token_pattern=None  # type: ignore
    )  # type: ignore
    tfidf_matrix = vectorizer.fit_transform(values)
    return cosine_similarity(tfidf_matrix)


def score_normalize(score: np.float64, precision=5) -> int | float:
    """Convert a similarity score from numpy float either a 1 integer
    (if >=1 or 0) or a float"""
    # Convert value to Python int or float based on rules
    if score == 0:
        return 0
    if score >= 1:
        return 1
    return round(float(score), precision)


def similarity_matrix_to_tuples(
    similarity_matrix,
    indexes: list | None = None,
) -> list[tuple[int, int, float]]:
    """Convertit une matrice de similarité
    en une liste de tuples (index_a, index_b, score)
    Optionnel: on peut passer une liste d'indexes à
    mapper avec la matrix, par exemple pour mapper des indexes
    à des identifiants, des indexes non contigus, etc.
    """
    indices = np.triu_indices_from(similarity_matrix, k=1)
    tuples = [
        (int(i), int(j), score_normalize(similarity_matrix[i, j]))
        for i, j in zip(*indices)
    ]
    tuples.sort(key=lambda x: x[2], reverse=True)
    if indexes:
        tuples = [(indexes[i], indexes[j], score) for i, j, score in tuples]
    return tuples


def score_tuples_to_clusters(
    tuples: list[tuple[int, int, float]], threshold
) -> list[list[int]]:
    """Convertit une liste de tuples d'acteurs (index_a, index_b, score) en clusters"""

    # On ne devrait jamais converver des clusters vides, donc si on appelle
    # cette fonction avec une liste vide, c'est qu'on a un problème
    # en amont
    if not tuples:
        raise ValueError("Liste de tuples d'entrée vide, on ne devrait pas être ici")

    # Trier la liste par score décroissant même si elle est déjà triée
    # car cela n'est pas garanti par l'appelant ET nous avons
    # une optimisation avec "break" dans la boucle
    tuples.sort(key=lambda x: x[2], reverse=True)

    clusters = []
    for index_a, index_b, score in tuples:
        # Ayant trié la liste par score décroissant, on peut sortir
        # de la boucle dès qu'on a un score inférieur au seuil
        if score < threshold:
            break

        # On cherche si index_a ou index_b sont déjà dans un cluster
        cluster_a = next((c for c in clusters if index_a in c), None)
        cluster_b = next((c for c in clusters if index_b in c), None)

        # a et b sont déjà dans un cluster: on les fusionne
        if cluster_a and cluster_b:
            if cluster_a != cluster_b:
                # Merge the clusters if they are different
                cluster_a.update(cluster_b)
                clusters.remove(cluster_b)
        # a est dans un cluster, on ajoute b dedans
        elif cluster_a:
            cluster_a.add(index_b)
        # b est dans un cluster, on ajoute a dedans
        elif cluster_b:
            cluster_b.add(index_a)
        else:
            # a et b ne sont dans aucun cluster: on crée un nouveau cluster
            clusters.append(set([index_a, index_b]))

    return [list(cluster) for cluster in clusters]


def cluster_to_subclusters(
    df: pd.DataFrame,
    column: str,
    cluster: list[int],
    threshold: float,
) -> list[list[int]]:
    """Scinde un cluster en 1+ sous-clusters en fonction de la similarité des valeurs
    d'une colonne donnée. On s'assure qu'il n'y a pas de sous-clusters dupliqués."""
    # logger.info(f"\n\nrefine_cluster, {column=}, {cluster=}, {threshold=}")
    df_cluster = df.loc[cluster]
    column_values = df_cluster[column].astype(str).values
    similarity_matrix = values_to_similarity_matrix(column_values)  # type: ignore
    tuples = similarity_matrix_to_tuples(similarity_matrix, indexes=cluster)

    # Debug
    """
    for i, j, score in tuples:
        symbol = "🟢" if score >= threshold else "🔴"
        v_i = column_values[cluster.index(i)]
        v_j = column_values[cluster.index(j)]
        # logger.info(f"{symbol} {i=}, {j=}, {v_i=}, {v_j=} {score=}")
    """

    sub_clusters = score_tuples_to_clusters(tuples, threshold)
    # logger.info(f"{sub_clusters=}")
    return sub_clusters


def cluster_cols_group_fuzzy(df_src, columns, threshold):

    # Initialize with all rows as a single cluster
    df = df_src.copy()
    for column in columns:
        # Remove rows with None or empty string values
        df = df.dropna(subset=[column])
        df = df[df[column].astype(str).str.strip() != ""]

    # On ne considère que les clusters de taille 2+
    if len(df) < 2:
        return []

    clusters = [list(df.index)]

    for column in columns:
        clusters_ref = []
        for cluster in clusters:
            clusters_ref_new = cluster_to_subclusters(df, column, cluster, threshold)
            # logger.info(f"{column=}, {cluster=}, {clusters_ref_new=}")
            clusters_ref.extend(clusters_ref_new)

        # Only continue with valid clusters for the next refinement step
        clusters = [cluster for cluster in clusters_ref if len(cluster) > 1]

    # Convert clusters into DataFrames
    result_dfs = [df.loc[cluster].reset_index(drop=True) for cluster in clusters]

    return result_dfs


def cluster_acteurs_clusters(
    df: pd.DataFrame,
    cluster_fields_exact: list[str] = [],
    cluster_fields_fuzzy: list[str] = [],
    cluster_fields_separate: list[str] = [],
    cluster_fuzzy_threshold: float = 0.5,
    cluster_intra_source_is_allowed: bool = False,
) -> pd.DataFrame:
    """
    Génère des suggestions de clusters sur un DataFrame

    Args:
        df: DataFrame à clusteriser
        cluster_fields_exact: champs pour grouper en 1 cluster si identique
        cluster_fields_fuzzy: champs pour grouper en 1 cluster si similaire
        cluster_fields_separate: champs pour séparer en plusieurs clusters si identique

    Returns:
        DataFrame de cluster_id -> identifiant_unique
    """

    if COL_INDEX_SRC not in df.columns:
        raise ValueError(
            """La colonne '__index_src' doit être ajoutée à df
                pour faire le lien avant/après clusterisation"""
        )

    # Vérification des colonnes
    for col in cluster_fields_exact:
        if col not in df.columns:
            raise ValueError(f"Colonne match exacte '{col}' pas dans le DataFrame")
    for col in cluster_fields_fuzzy:
        if col not in df.columns:
            raise ValueError(f"Colonne match fuzzy '{col}' pas dans le DataFrame")

    # On supprime les lignes avec des valeurs nulles pour les colonnes exact
    # TODO: subtilités à gérer, ex on peut pas drop sur cluster_fields_separate
    # à cause de source_id qui nulle sur les parents, on devrait certainement
    # définir config.fields_to_drop_na avec des tests pour + de robustesse
    df = df.dropna(subset=cluster_fields_exact + cluster_fields_fuzzy)
    # Ordonne df sur les colonnes exactes
    df = df.sort_values(cluster_fields_exact)

    # On ne garde que les colonnes utiles
    cols_ids_codes = [
        col for col in df.columns if re.search(r"identifiant|_code|_id", col, re.I)
    ]
    cols_to_keep = list(
        set(
            cols_ids_codes
            + cluster_fields_exact
            + cluster_fields_separate
            + cluster_fields_fuzzy
            + [COL_INDEX_SRC]
            + ["nom"]
        )
    )
    # logger.info(f"{cols_to_keep=}")
    df = df[cols_to_keep]

    # On groupe par les colonnes exactes
    clusters_size1 = []
    clusters = []
    for exact_keys, exact_rows in df.groupby(cluster_fields_exact):
        logger.info("\n\n")
        # On ne considère que les clusters de taille 2+
        if len(exact_rows) < 2:
            logger.info(f"🔴 Ignoré: cluster de taille <2: {list(exact_keys)}")
            clusters_size1.append(exact_keys)
            continue
        keys = list(exact_keys)

        log.preview_df_as_markdown("🔵 Cluster potentiel exact", exact_rows)

        # Liste des clusters à considérer, on commence avec rien
        clusters_potential = []

        # Fuzzy clustering activated
        if cluster_fields_fuzzy:
            keys += cluster_fields_fuzzy
            subclusters = cluster_cols_group_fuzzy(
                exact_rows, cluster_fields_fuzzy, threshold=cluster_fuzzy_threshold
            )
            cnt = len(subclusters)
            status = "🔵" if cnt else "🔴"
            logger.info(f"{status} Après fuzzy: #{cnt} sous-clusters")
            for i, fuzzy_rows in enumerate(subclusters):
                fuzzy_keys = keys + [str(i + 1)]
                clusters_potential.append(("fuzzy", fuzzy_keys, fuzzy_rows))

        else:
            # Fuzzy clustering not activated
            clusters_potential.append(("exact", keys, exact_rows))

        # For all potential clusters, we apply the intra-source logic
        for ctype, keys, rows in clusters_potential:
            cluster_id = cluster_id_from_strings(keys)
            rows["cluster_id"] = cluster_id
            values = rows[cluster_fields_fuzzy + ["nom"]]
            logger.info(f"\n🟢 CLUSTER: {cluster_id=}, {keys=}, {values=}")

            if cluster_intra_source_is_allowed:
                clusters.append(rows.copy())
            else:
                kept, lost = cluster_exclude_intra_source(rows)
                if isinstance(lost, pd.DataFrame):
                    log.preview_df_as_markdown("❌ Acteurs intra-source exclus", lost)
                if len(kept) < 2:
                    log.preview_df_as_markdown("🔴 Cluster de taille <2", kept)
                    continue
                log.preview_df_as_markdown(f"🟢 Cluster {ctype} conservé", kept)
                clusters.append(kept.copy())

    if not clusters:
        return pd.DataFrame()

    # On combine tous les clusters ensemble
    df_clusters = pd.concat(clusters)

    # On ne garde que les clusters de taille 2+
    df_clusters = df_clusters.groupby("cluster_id").filter(lambda x: len(x) >= 2)

    # TODO: définir plusieurs type d'acteurs non perdus
    # (intra source, manque de similarité, etc)
    # et retourner in dict pour pouvoir afficher dans airflow
    # df_lost = pd.concat(dfs_lost) if dfs_lost else None
    logger.info(f"🟢 {len(clusters_size1)=}")
    logger.info(f"🟢 {df_clusters["cluster_id"].nunique()=}")
    logger.info(f"🟢 {df_clusters["identifiant_unique"].nunique()=}")

    return df_clusters
