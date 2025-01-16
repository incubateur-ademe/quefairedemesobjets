"""
Fonctions de clustering des acteurs

TODO: améliorer le debug: en mode CLI on avant des print()
qui étaient suffisants, mais en mode Airflow, on va faire
exploser la taille des logs, donc on a besoin de refactorer:
 - les fonctions doivent retourner des valeurs de debug
 - ces valeurs de debug vont être remontées à Airflow
 - dans airflow on pourra utiliser nos utilitaires genre log.preview()
    qui afficheront une partie du debug
"""

import json
import re

import numpy as np
import pandas as pd
from rich import print
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from slugify import slugify
from unidecode import unidecode

COLS_GROUP_EXACT_ALWAYS = [
    # "code_departement",
    "code_postal",
]


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
    vectorizer = TfidfVectorizer(tokenizer=str.split, binary=False)
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
    vectorizer = TfidfVectorizer(tokenizer=str.split, binary=False)
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
    print(f"{tuples=}")
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
    print("\n\nrefine_cluster", f"{column=}, {cluster=}, {threshold=}")
    df_cluster = df.loc[cluster]
    column_values = df_cluster[column].astype(str).values
    similarity_matrix = values_to_similarity_matrix(column_values)  # type: ignore
    tuples = similarity_matrix_to_tuples(similarity_matrix, indexes=cluster)

    # Debug
    for i, j, score in tuples:
        symbol = "🟢" if score >= threshold else "🔴"
        v_i = column_values[cluster.index(i)]
        v_j = column_values[cluster.index(j)]
        print(f"{symbol} {i=}, {j=}, {v_i=}, {v_j=} {score=}")

    sub_clusters = score_tuples_to_clusters(tuples, threshold)
    print(f"{sub_clusters=}")
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
            print(f"{column=}, {cluster=}, {clusters_ref_new=}")
            clusters_ref.extend(clusters_ref_new)

        # Only continue with valid clusters for the next refinement step
        clusters = [cluster for cluster in clusters_ref if len(cluster) > 1]

    # Convert clusters into DataFrames
    result_dfs = [df.loc[cluster].reset_index(drop=True) for cluster in clusters]

    return result_dfs


def cluster_acteurs_suggestions(
    df: pd.DataFrame,
    cluster_fields_exact: list[str] = [],
    cluster_fields_fuzzy: list[str] = [],
    cluster_fields_separate: list[str] = [],
    cluster_fuzzy_threshold: float = 0.5,
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
    if "__index_src" not in df.columns:
        raise ValueError(
            """La colonne '__index_src' doit être ajoutée à df
                pour faire le lien avant/après clusterisation"""
        )

    # Vérification des colonnes
    for col in COLS_GROUP_EXACT_ALWAYS + cluster_fields_exact:
        if col not in df.columns:
            raise ValueError(f"Colonne match exacte '{col}' pas dans le DataFrame")
    for col in cluster_fields_fuzzy:
        if col not in df.columns:
            raise ValueError(f"Colonne match fuzzy '{col}' pas dans le DataFrame")

    # On supprime les lignes avec des valeurs nulles pour les colonnes exact
    df = df.dropna(
        subset=COLS_GROUP_EXACT_ALWAYS
        + cluster_fields_exact
        + cluster_fields_separate
        + cluster_fields_fuzzy
    )
    # Ordonne df sur les colonnes exactes
    df = df.sort_values(COLS_GROUP_EXACT_ALWAYS + cluster_fields_exact)

    # On ne garde que les colonnes utiles
    cols_ids_codes = [
        col for col in df.columns if re.search(r"identifiant|_code|_id", col, re.I)
    ]
    cols_to_keep = list(
        set(
            COLS_GROUP_EXACT_ALWAYS
            + cols_ids_codes
            + cluster_fields_exact
            + cluster_fields_separate
            + cluster_fields_fuzzy
            + ["__index_src"]
            + ["nom"]
        )
    )
    print(f"{cols_to_keep=}")
    df = df[cols_to_keep]

    # On groupe par les colonnes exactes
    clusters_size1 = []
    clusters = []
    for exact_keys, exact_rows in df.groupby(
        COLS_GROUP_EXACT_ALWAYS + cluster_fields_exact
    ):
        # On ne considère que les clusters de taille 2+
        if len(exact_rows) < 2:
            print(f"🔴 Ignoré: cluster de taille <2: {list(exact_keys)}")
            clusters_size1.append(exact_keys)
            continue
        keys = list(exact_keys)

        # TODO: à déplacer après la logique de clustering
        # pour pouvoir sélectionner l'acteur avec le meilleur match
        if cluster_fields_separate:
            # Le cas où on cherche à séparer les clusters
            # On cherche d'abord à voir si dans le groupe existant (exact_rows)
            # Si c'est le cas, on les sépare en plusieurs clusters
            for _, rows_split in exact_rows.groupby(cluster_fields_separate):
                if len(rows_split) > 1:
                    # TODO: gérer le cas split, pour l'instant on exclue juste
                    # toutes les lignes sauf la première
                    exact_rows = exact_rows.drop(rows_split.index[1:])

        # On ne considère que les clusters de taille 2+
        if len(exact_rows) < 2:
            continue

        # Liste des clusters à considérer, on commence avec rien
        clusters_to_add = []

        print(f"🟡 Cluster potentiel avant fuzzy: taille {len(exact_rows)}")
        fields_debug = (
            cluster_fields_exact + cluster_fields_fuzzy + ["identifiant_unique"]
        )
        print(json.dumps(exact_rows[fields_debug].to_dict(orient="list"), indent=4))

        # Si on a des champs fuzzy, on cherche à
        # sous-clusteriser sur ces champs
        if cluster_fields_fuzzy:
            print(f"fields_fuzzy={cluster_fields_fuzzy}")
            print(f"threshold={cluster_fuzzy_threshold}")

            keys += cluster_fields_fuzzy
            subclusters = cluster_cols_group_fuzzy(
                exact_rows, cluster_fields_fuzzy, threshold=cluster_fuzzy_threshold
            )
            print(f"Sous-clusters après fuzzy: {len(subclusters)} sous-clusters")
            for i, fuzzy_rows in enumerate(subclusters):
                fuzzy_keys = keys + [str(i + 1)]
                print("🟢 Sous-cluster conservé:")
                print(json.dumps(fuzzy_rows.to_dict(orient="list"), indent=4))
                clusters_to_add.append((fuzzy_keys, fuzzy_rows))

        else:
            print("🟢 Cluster conservé (sur la base des champs exacts uniquement)")
            print(exact_rows)
            clusters_to_add.append((keys, exact_rows))

        for keys, rows in clusters_to_add:
            cluster_id = cluster_id_from_strings(keys)
            rows["cluster_id"] = cluster_id
            values = rows[cluster_fields_fuzzy + ["nom"]]
            print(f"\n🟢 CLUSTER: {cluster_id=}, {keys=}, {values=}")
            clusters.append(rows.copy())

    if not clusters:
        return pd.DataFrame()

    # On combine tous les clusters ensemble
    df_clusters = pd.concat(clusters)

    # On ne garde que les clusters de taille 2+
    df_clusters = df_clusters.groupby("cluster_id").filter(lambda x: len(x) >= 2)

    """
    # Debug pour les clusters de taille 1
    print("🔴 clusters_size1", clusters_size1)
    df_clusters_1 = pd.DataFrame(
        clusters_size1, columns=COLS_GROUP_EXACT_ALWAYS + cluster_fields_exact
    )

    # Show entries grouped by code_postal and acteur_type_code which have >1 entries
    issues_villes = df_clusters_1.groupby(["code_postal"]).filter(lambda x: len(x) >= 2)

    print(f"🔴 {issues_villes=}")
    """
    print(f"🟢 {len(clusters_size1)=}")
    print(f"🟢 {df_clusters["cluster_id"].nunique()=}")
    print(f"🟢 {df_clusters["identifiant_unique"].nunique()=}")

    return df_clusters
