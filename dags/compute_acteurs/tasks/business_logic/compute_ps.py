import pandas as pd
from utils import logging_utils as log


def compute_ps(
    df_ps: pd.DataFrame,
    df_rps: pd.DataFrame,
    df_ps_sscat: pd.DataFrame,
    df_rps_sscat: pd.DataFrame,
    df_revisionacteur: pd.DataFrame,
):
    df_rps_sscat = df_rps_sscat.rename(
        columns={"revisionpropositionservice_id": "propositionservice_id"}
    )
    df_rps = df_rps.rename(columns={"revision_acteur_id": "acteur_id"})

    # Remove the propositionservice for the acteur that have a revision
    df_ps = df_ps[~df_ps["acteur_id"].isin(df_revisionacteur["identifiant_unique"])]

    # Proposition de service de acteur et de revisionacteur mergées
    df_ps_merged = pd.concat(
        [
            # Remove the ps for the acteur that have a revision
            df_ps,
            df_rps,
        ],
        ignore_index=True,
    )

    rps_ids = df_rps["id"].unique()
    ps_ids = df_ps["id"].unique()

    df_rps_sscat = df_rps_sscat[df_rps_sscat["propositionservice_id"].isin(rps_ids)]
    df_ps_sscat = df_ps_sscat[df_ps_sscat["propositionservice_id"].isin(ps_ids)]
    df_ps_sscat_merged = pd.concat(
        [
            df_rps_sscat,
            df_ps_sscat,
        ],
        ignore_index=True,
    )
    log.preview("Result df_ps_merged", df_revisionacteur)
    log.preview(
        "Result df_ps_sscat_merged",
        df_ps_sscat_merged,
    )

    return {
        "df_ps_merged": df_ps_merged,
        "df_ps_sscat_merged": (df_ps_sscat_merged),
    }
