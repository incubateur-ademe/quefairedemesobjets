import pandas as pd


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
