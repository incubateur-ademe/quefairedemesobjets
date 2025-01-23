import pandas as pd
import shortuuid
from sources.config import shared_constants as constants


def compute_acteur(df_acteur: pd.DataFrame, df_revisionacteur: pd.DataFrame):

    revisionacteur_parent_ids = df_revisionacteur["parent_id"].unique()

    df_revisionacteur_parents = df_revisionacteur[
        df_revisionacteur["identifiant_unique"].isin(revisionacteur_parent_ids)
    ]

    df_acteur = df_acteur.set_index("identifiant_unique")
    df_revisionacteur = df_revisionacteur.set_index("identifiant_unique")
    # suppression du if et ajout de errors="ignore" pour éviter les erreurs
    df_revisionacteur = df_revisionacteur.drop(columns=["cree_le"], errors="ignore")
    df_acteur.update(df_revisionacteur)

    df_acteur_merged = pd.concat(
        [df_acteur, df_revisionacteur_parents.set_index("identifiant_unique")]
    ).reset_index()
    df_children = (
        df_revisionacteur.reset_index()
        .query("parent_id.notnull()")
        .drop_duplicates(subset=["parent_id", "identifiant_unique"])
    )

    all_parent_ids = set(df_acteur_merged["parent_id"].tolist())
    df_children = df_children[df_children["statut"] == constants.ACTEUR_ACTIF]
    active_parent_ids = set(df_acteur_merged["parent_id"].tolist())
    parent_without_children_ids = all_parent_ids - active_parent_ids

    # Get children
    df_children = pd.merge(
        df_children[["parent_id", "identifiant_unique"]],
        df_acteur_merged[["identifiant_unique", "source_id"]],
        on="identifiant_unique",
    )

    # Remove children from acteur_merged
    df_acteur_merged = df_acteur_merged[
        ~df_acteur_merged["identifiant_unique"].isin(
            df_children["identifiant_unique"].tolist()
        )
    ].copy()

    # Remove parent without children
    df_acteur_merged = df_acteur_merged[
        ~df_acteur_merged["identifiant_unique"].isin(parent_without_children_ids)
    ]

    # Remove inactive acteur
    df_acteur_merged = df_acteur_merged[
        df_acteur_merged["statut"] == constants.ACTEUR_ACTIF
    ]

    # Add a new column uuid to make the displayedacteur id without source name in id
    df_acteur_merged["uuid"] = df_acteur_merged["identifiant_unique"].apply(
        lambda x: shortuuid.uuid(name=x)
    )

    return {
        "df_acteur_merged": df_acteur_merged,
        # ["parent_id", "child_id", "child_source_id"]
        "df_children": df_children[
            ["parent_id", "identifiant_unique", "source_id"]
        ].reset_index(drop=True),
    }
