import pandas as pd
from utils import logging_utils as log


def split_clusters_infra_source(
    clusters_potential: list[tuple[str, list[str], pd.DataFrame]],
):
    result = []
    for ctype, keys, rows in clusters_potential:
        result = result + split_cluster_intra_source((ctype, keys, rows))
    return result


def split_cluster_intra_source(
    cluster_potential: tuple[str, list[str], pd.DataFrame],
    index_to_add: int = 0,
) -> list[tuple[str, list[str], pd.DataFrame]]:
    (ctype, keys, rows) = cluster_potential

    # Ordonner rows pour commencer par ceux qui on le plus de source_codes
    rows["nb_sources"] = rows["source_codes"].apply(len)
    rows = rows.sort_values(by="nb_sources", ascending=False)

    source_codes = set()
    current_rows = pd.DataFrame()
    new_rows = pd.DataFrame()

    for row in rows.to_dict(orient="records"):
        # intersection between source_codes and row["source_codes"]
        if source_codes.intersection(set(row["source_codes"])):
            new_rows = pd.concat([new_rows, pd.DataFrame([row])], ignore_index=True)
        else:
            source_codes = source_codes.union(set(row["source_codes"]))
            current_rows = pd.concat(
                [current_rows, pd.DataFrame([row])], ignore_index=True
            )

    if len(new_rows) < 2:
        if len(new_rows) == 1:
            log.preview_df_as_markdown("❌ Acteurs intra-source exclus", new_rows)
            # FIXME : ajout de message, le news_rows de 1 est ignoré
            pass
        if index_to_add:
            keys.append(str(index_to_add))
        return [(ctype, keys, current_rows)]
    else:
        copy_keys = keys.copy()
        if index_to_add:
            keys.append(str(index_to_add))
        return [(ctype, keys, current_rows)] + split_cluster_intra_source(
            (ctype, copy_keys, new_rows), index_to_add + 1
        )


def cluster_exclude_intra_source(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Exclude intra-source actors from a cluster. Returns 2 dfs:
    - original without duplication on sources
    - another df with excluded actors"""

    # Restrict usage of function to single cluster (simplifies logic)
    if not df["cluster_id"].nunique() == 1:
        raise ValueError("Fonction à utiliser sur 1 seul cluster")

    # Parents have not source thus ignored
    df_children = df[df["source_id"].notnull()]
    df_parents = df[df["source_id"].isnull()]

    # No duplication on sources -> return original df as is
    if df_children["source_id"].nunique() == len(df_children):
        return df, None

    # For each source, keep only one actor
    # TODO: could be improved with similarity scores
    df_children_kept = df_children.groupby("source_id").first().reset_index()

    # Final results: acteurs kept vs. excluded
    id = "identifiant_unique"
    df_kept = pd.concat([df_children_kept, df_parents], ignore_index=True)
    df_lost = df_children[~df_children[id].isin(df_kept[id])].reset_index(drop=True)

    return df_kept, df_lost
