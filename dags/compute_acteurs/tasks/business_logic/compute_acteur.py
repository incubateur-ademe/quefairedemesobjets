import pandas as pd
import shortuuid
from sources.config import shared_constants as constants
from utils.django import django_setup_full

django_setup_full()

from qfdmo.models.acteur import RevisionActeur  # noqa: E402


def compute_acteur(df_acteur: pd.DataFrame, df_revisionacteur: pd.DataFrame):

    # Collect parent_id among active revisionacteurs
    df_revisionacteur_parents = df_revisionacteur[
        df_revisionacteur["statut"] == constants.ACTEUR_ACTIF
    ]
    if "public_accueilli" in df_revisionacteur.columns:
        df_revisionacteur_parents = df_revisionacteur_parents[
            df_revisionacteur["public_accueilli"] != constants.PUBLIC_PRO
        ]
    revisionacteur_parent_ids = df_revisionacteur_parents["parent_id"].unique()

    df_revisionacteur_parents = df_revisionacteur[
        df_revisionacteur["identifiant_unique"].isin(revisionacteur_parent_ids)
    ]

    df_acteur = df_acteur.set_index("identifiant_unique")
    df_revisionacteur = df_revisionacteur.set_index("identifiant_unique")
    # suppression du if et ajout de errors="ignore" pour éviter les erreurs
    df_revisionacteur = df_revisionacteur.drop(columns=["cree_le"], errors="ignore")
    df_revisionacteur_for_update = df_revisionacteur.replace({"": pd.NA})
    df_acteur.update(df_revisionacteur_for_update)

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
    if "public_accueilli" in df_children.columns:
        df_children = df_children[
            df_children["public_accueilli"] != constants.PUBLIC_PRO
        ]

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
    if "public_accueilli" in df_acteur_merged.columns:
        df_acteur_merged = df_acteur_merged[
            df_acteur_merged["public_accueilli"] != constants.PUBLIC_PRO
        ]

    # Add a new column uuid to make the displayedacteur id without source name in id
    df_acteur_merged["uuid"] = df_acteur_merged["identifiant_unique"].apply(
        lambda x: shortuuid.uuid(name=x)
    )

    # Get all charfield of Acteur model
    string_fields = {
        field.name
        for field in RevisionActeur._meta.get_fields()
        if field.get_internal_type() in ["CharField", "TextField"]
    } - {"identifiant_unique", "statut"}
    # For each charfield, replace __empty__ by ""
    for string_field in string_fields:
        if string_field in df_acteur_merged.columns:
            df_acteur_merged[string_field] = df_acteur_merged[string_field].replace(
                constants.EMPTY_ACTEUR_FIELD, ""
            )

    return {
        "df_acteur_merged": df_acteur_merged,
        # ["parent_id", "child_id", "child_source_id"]
        "df_children": df_children[
            ["parent_id", "identifiant_unique", "source_id"]
        ].reset_index(drop=True),
    }
