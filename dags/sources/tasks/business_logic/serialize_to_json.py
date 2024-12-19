import json
import logging

import pandas as pd
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_data_prepare(
    df_acteur_to_delete: pd.DataFrame,
    df_actors: pd.DataFrame,
    df_ps: pd.DataFrame,
    df_ps_sscat: pd.DataFrame,
    df_labels: pd.DataFrame,
    df_acteur_services: pd.DataFrame,
):
    update_actors_columns = ["identifiant_unique", "statut", "cree_le"]
    df_acteur_to_delete["row_updates"] = df_acteur_to_delete[
        update_actors_columns
    ].apply(lambda row: json.dumps(row.to_dict(), default=str), axis=1)
    # Created or updated Acteurs
    df_acteur_services = (
        df_acteur_services
        if df_acteur_services is not None
        else pd.DataFrame(columns=["acteur_id", "acteurservice_id"])
    )

    if df_actors.empty:
        raise ValueError("df_actors est vide")
    if df_ps.empty:
        raise ValueError("df_ps est vide")
    if df_ps_sscat.empty:
        raise ValueError("df_ps_sscat est vide")

    aggregated_psc = (
        df_ps_sscat.groupby("propositionservice_id")
        .apply(lambda x: x.to_dict("records") if not x.empty else [])
        .reset_index(name="ps_sscat")
    )

    df_ps_joined = pd.merge(
        df_ps,
        aggregated_psc,
        how="left",
        left_on="id",
        right_on="propositionservice_id",
    )
    df_ps_joined["propositionservice_id"] = df_ps_joined[
        "propositionservice_id"
    ].astype(str)

    df_ps_joined["ps_sscat"] = df_ps_joined["ps_sscat"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    df_ps_joined.drop("id", axis=1, inplace=True)

    aggregated_ps = (
        df_ps_joined.groupby("acteur_id")
        .apply(lambda x: x.to_dict("records") if not x.empty else [])
        .reset_index(name="proposition_services")
    )

    aggregated_labels = df_labels.groupby("acteur_id").apply(
        lambda x: x.to_dict("records") if not x.empty else []
    )
    aggregated_labels = (
        pd.DataFrame(columns=["acteur_id", "labels"])
        if aggregated_labels.empty
        else aggregated_labels.reset_index(name="labels")
    )

    aggregated_acteur_services = df_acteur_services.groupby("acteur_id").apply(
        lambda x: x.to_dict("records") if not x.empty else []
    )
    aggregated_acteur_services = (
        pd.DataFrame(columns=["acteur_id", "acteur_services"])
        if aggregated_acteur_services.empty
        else aggregated_acteur_services.reset_index(name="acteur_services")
    )

    df_joined_with_ps = pd.merge(
        df_actors,
        aggregated_ps,
        how="left",
        left_on="identifiant_unique",
        right_on="acteur_id",
    )

    df_joined_with_labels = pd.merge(
        df_joined_with_ps,
        aggregated_labels,
        how="left",
        left_on="acteur_id",
        right_on="acteur_id",
    )

    df_joined = pd.merge(
        df_joined_with_labels,
        aggregated_acteur_services,
        how="left",
        left_on="acteur_id",
        right_on="acteur_id",
    )

    df_joined["proposition_services"] = df_joined["proposition_services"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    df_joined.loc[
        df_joined["proposition_services"].apply(lambda x: x == []), "statut"
    ] = "INACTIF"

    df_joined.drop("acteur_id", axis=1, inplace=True)

    df_joined = df_joined.where(pd.notna(df_joined), None)

    df_joined["row_updates"] = df_joined.apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )
    df_joined.drop_duplicates("identifiant_unique", keep="first", inplace=True)
    log.preview("df_joined", df_joined)
    log.preview("df_acteur_to_delete", df_acteur_to_delete)

    return {"all": {"df": df_joined}, "to_disable": {"df": df_acteur_to_delete}}
