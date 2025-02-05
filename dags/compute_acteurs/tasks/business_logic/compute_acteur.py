import pandas as pd
import shortuuid
from sources.config import shared_constants as constants
from utils.django import django_setup_full

django_setup_full()

from qfdmo.models.acteur import RevisionActeur  # noqa: E402


def compute_acteur(df_acteur: pd.DataFrame, df_revisionacteur: pd.DataFrame):

    revisionacteur_parent_ids = df_revisionacteur["parent_id"].unique()

    df_revisionacteur_parents = df_revisionacteur[
        df_revisionacteur["id"].isin(revisionacteur_parent_ids)
    ]

    df_acteur = df_acteur.set_index("id")
    df_revisionacteur = df_revisionacteur.set_index("id")
    # suppression du if et ajout de errors="ignore" pour éviter les erreurs
    df_revisionacteur = df_revisionacteur.drop(columns=["cree_le"], errors="ignore")
    df_acteur.update(df_revisionacteur)

    df_acteur_merged = pd.concat(
        [df_acteur, df_revisionacteur_parents.set_index("id")]
    ).reset_index()
    df_children = (
        df_revisionacteur.reset_index()
        .query("parent_id.notnull()")
        .drop_duplicates(subset=["parent_id", "id"])
    )

    all_parent_ids = set(df_acteur_merged["parent_id"].tolist())
    df_children = df_children[df_children["statut"] == constants.ACTEUR_ACTIF]
    active_parent_ids = set(df_acteur_merged["parent_id"].tolist())
    parent_without_children_ids = all_parent_ids - active_parent_ids

    # Get children
    df_children = pd.merge(
        df_children[["parent_id", "id"]],
        df_acteur_merged[["id", "source_id"]],
        on="id",
    )

    # Remove children from acteur_merged
    df_acteur_merged = df_acteur_merged[
        ~df_acteur_merged["id"].isin(df_children["id"].tolist())
    ].copy()

    # Remove parent without children
    df_acteur_merged = df_acteur_merged[
        ~df_acteur_merged["id"].isin(parent_without_children_ids)
    ]

    # Remove inactive acteur
    df_acteur_merged = df_acteur_merged[
        df_acteur_merged["statut"] == constants.ACTEUR_ACTIF
    ]

    # Add a new column uuid to make the displayedacteur id without source name in id
    df_acteur_merged["uuid"] = df_acteur_merged["id"].apply(
        lambda x: shortuuid.uuid(name=x)
    )

    # Get all charfield of Acteur model
    string_fields = {
        field.name
        for field in RevisionActeur._meta.get_fields()
        if field.get_internal_type() in ["CharField", "TextField"]
    } - {"id", "statut"}
    # For each charfield, replace __empty__ by ""
    for string_field in string_fields:
        if string_field in df_acteur_merged.columns:
            df_acteur_merged[string_field] = df_acteur_merged[string_field].replace(
                constants.EMPTY_ACTEUR_FIELD, ""
            )

    return {
        "df_acteur_merged": df_acteur_merged,
        # ["parent_id", "child_id", "child_source_id"]
        "df_children": df_children[["parent_id", "id", "source_id"]].reset_index(
            drop=True
        ),
    }
