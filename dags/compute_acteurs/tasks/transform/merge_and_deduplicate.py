import pandas as pd


def deduplicate_acteurs_many2many_relationship(
    df_children: pd.DataFrame, df_merged_relationship: pd.DataFrame, col: str
) -> pd.DataFrame:

    # Keep only the relationship of the children
    df_children_relationship = df_children.merge(
        df_merged_relationship,
        left_on="identifiant_unique",
        right_on="displayedacteur_id",
        how="inner",
    )

    # Deduplicate the relationship : renaming parent_id to displayedacteur_id
    df_children_relationship.drop(columns=["displayedacteur_id"], inplace=True)
    df_children_relationship.drop_duplicates(
        subset=["parent_id", col], keep="first", inplace=True
    )
    df_children_relationship.rename(
        columns={"parent_id": "displayedacteur_id"}, inplace=True
    )

    df_relationship = pd.concat(
        [df_merged_relationship, df_children_relationship[["displayedacteur_id", col]]],
        ignore_index=True,
    )
    df_relationship = df_relationship[
        ~df_relationship["displayedacteur_id"].isin(
            df_children["identifiant_unique"].tolist()
        )
    ]

    return df_relationship


def merge_acteurs_many2many_relationship(
    df_link_with_acteur: pd.DataFrame,
    df_link_with_revisionacteur: pd.DataFrame,
    df_revisionacteur: pd.DataFrame,
):
    # Remove the link_with_acteur for the acteur that have a revision
    df_link_with_acteur = df_link_with_acteur[
        ~df_link_with_acteur["acteur_id"].isin(df_revisionacteur["identifiant_unique"])
    ].copy()

    # Rename 'acteur_id' column to 'displayedacteur_id' and drop 'id' column
    df_link_with_acteur.rename(
        columns={"acteur_id": "displayedacteur_id"}, inplace=True
    )
    df_link_with_acteur.drop(columns=["id"], inplace=True)

    # Rename 'revisionacteur_id' column to 'displayedacteur_id' and drop 'id' column
    df_link_with_revisionacteur.rename(
        columns={"revisionacteur_id": "displayedacteur_id"}, inplace=True
    )
    df_link_with_revisionacteur.drop(columns=["id"], inplace=True)

    # Concatenate dataframes excluding common 'displayedacteur_id' in df_actor
    df_link_with_acteur_merged = pd.concat(
        [
            df_link_with_acteur,
            df_link_with_revisionacteur,
        ]
    ).drop_duplicates()

    return df_link_with_acteur_merged
