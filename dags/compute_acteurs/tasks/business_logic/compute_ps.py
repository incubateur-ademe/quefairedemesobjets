import pandas as pd
from utils import logging_utils as log


def compute_ps(
    df_propositionservice: pd.DataFrame,
    df_revisionpropositionservice: pd.DataFrame,
    df_propositionservice_sous_categories: pd.DataFrame,
    df_revisionpropositionservice_sous_categories: pd.DataFrame,
    df_revisionacteur: pd.DataFrame,
):
    # old apply_corrections_propositionservices

    df_revisionpropositionservice_sous_categories = (
        df_revisionpropositionservice_sous_categories.rename(
            columns={"revisionpropositionservice_id": "propositionservice_id"}
        )
    )
    df_revisionpropositionservice = df_revisionpropositionservice.rename(
        columns={"revision_acteur_id": "acteur_id"}
    )

    # Remove the propositionservice for the acteur that have a revision
    df_propositionservice = df_propositionservice[
        ~df_propositionservice["acteur_id"].isin(
            df_revisionacteur["identifiant_unique"]
        )
    ]

    # Proposition de service de acteur et de revisionacteur mergées
    df_propositionservice_merged = pd.concat(
        [
            # Remove the propositionservice for the acteur that have a revision
            df_propositionservice,
            df_revisionpropositionservice,
        ],
        ignore_index=True,
    )

    revisionpropositionservice_ids = df_revisionpropositionservice["id"].unique()
    propositionservice_ids = df_propositionservice["id"].unique()

    df_revisionpropositionservice_sous_categories = (
        df_revisionpropositionservice_sous_categories[
            df_revisionpropositionservice_sous_categories["propositionservice_id"].isin(
                revisionpropositionservice_ids
            )
        ]
    )
    df_propositionservice_sous_categories = df_propositionservice_sous_categories[
        df_propositionservice_sous_categories["propositionservice_id"].isin(
            propositionservice_ids
        )
    ]
    df_propositionservice_sous_categories_merged = pd.concat(
        [
            df_revisionpropositionservice_sous_categories,
            df_propositionservice_sous_categories,
        ],
        ignore_index=True,
    )
    log.preview("Result df_propositionservice_merged", df_revisionacteur)
    log.preview(
        "Result df_propositionservice_sous_categories_merged",
        df_propositionservice_sous_categories_merged,
    )

    return {
        "df_propositionservice_merged": df_propositionservice_merged,
        "df_propositionservice_sous_categories_merged": (
            df_propositionservice_sous_categories_merged
        ),
    }
