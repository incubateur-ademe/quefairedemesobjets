import pandas as pd


def deduplicate_acteur_sources(
    df_children: pd.DataFrame,
    df_acteur_merged: pd.DataFrame,
):

    df_acteur_sources_without_parents = df_acteur_merged[
        ~df_acteur_merged["identifiant_unique"].isin(df_children["parent_id"])
    ][["identifiant_unique", "source_id"]]

    df_acteur_sources_without_parents = df_acteur_sources_without_parents.rename(
        columns={"identifiant_unique": "displayedacteur_id"}
    )

    parents_df = df_children[["parent_id", "source_id"]].drop_duplicates()

    parents_df = parents_df.rename(columns={"parent_id": "displayedacteur_id"})

    result_df = pd.concat(
        [df_acteur_sources_without_parents, parents_df], ignore_index=True
    )

    result_df = result_df[
        ~result_df["displayedacteur_id"].isin(
            df_children["identifiant_unique"].tolist()
        )
    ]

    return result_df
