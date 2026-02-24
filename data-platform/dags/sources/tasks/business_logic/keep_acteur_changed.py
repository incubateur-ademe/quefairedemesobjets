import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from cluster.config.metadata import (
    METADATA_ANONYMIZED_ACTEURS_IGNORED,
    METADATA_NUMBER_OF_UPDATES_BY_FIELD,
)
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.transform.transform_df import compute_identifiant_unique
from utils.django import django_setup_full, get_model_fields

from data.models.changes.acteur_rgpd_anonymize import VALUE_ANONYMIZED

logger = logging.getLogger(__name__)

django_setup_full()


@dataclass
class ColumnDiff:
    modif: int = 0
    sup: int = 0
    ajout: int = 0

    def add(self, values: list[int]) -> None:
        self.modif += values[0]
        self.sup += values[1]
        self.ajout += values[2]


class ActeurComparator:
    def __init__(self, columns_to_compare: set[str]):
        self.columns_to_compare = columns_to_compare - {"identifiant_unique"}
        self.metadata: dict[str, ColumnDiff] = {}

    def _list_field_changed(self, list_from_source: list, list_from_db: list) -> bool:
        return sorted(list_from_source) != sorted(list_from_db)

    def _perimetre_adomiciles_changed(
        self, pad_from_source: list, pad_from_db: list
    ) -> bool:
        sorted_pad_from_source = sorted(
            pad_from_source, key=lambda x: (x["type"], x["valeur"])
        )
        sorted_pad_from_db = sorted(pad_from_db, key=lambda x: (x["type"], x["valeur"]))
        return sorted_pad_from_source != sorted_pad_from_db

    def _proposition_services_changed(
        self, ps_from_source: list[dict], ps_from_db: list[dict]
    ) -> bool:
        sorted_ps_from_source = sorted(ps_from_source, key=lambda x: x["action"])
        sorted_ps_from_db = sorted(ps_from_db, key=lambda x: x["action"])

        for item in sorted_ps_from_source:
            item["sous_categories"] = sorted(item["sous_categories"])
        for item in sorted_ps_from_db:
            item["sous_categories"] = sorted(item["sous_categories"])

        return sorted_ps_from_source != sorted_ps_from_db

    def _get_diff_type(self, source_val, db_val) -> list[int]:
        if not source_val:
            return [0, 1, 0]  # SUP
        if not db_val:
            return [0, 0, 1]  # AJOUT
        return [1, 0, 0]  # MODIF

    def field_changed(self, row_source: dict, row_db: dict) -> dict[str, list[int]]:
        columns_updated = {}
        for column in self.columns_to_compare:
            source_val = row_source[column]
            db_val = row_db[column]

            is_updated = False
            if column == "proposition_service_codes":
                is_updated = self._proposition_services_changed(source_val, db_val)
            elif column == "perimetre_adomicile_codes":
                is_updated = self._perimetre_adomiciles_changed(source_val, db_val)
            elif isinstance(source_val, list) and isinstance(db_val, list):
                is_updated = self._list_field_changed(source_val, db_val)
            elif isinstance(source_val, float) and isinstance(db_val, float):
                if np.isnan(source_val) and np.isnan(db_val):
                    is_updated = False
                else:
                    is_updated = source_val != db_val
            else:
                is_updated = source_val != db_val

            if is_updated:
                columns_updated[column] = self._get_diff_type(source_val, db_val)
                if column not in self.metadata:
                    self.metadata[column] = ColumnDiff()
                self.metadata[column].add(columns_updated[column])

        return columns_updated


def retrieve_identifiant_unique_from_existing_acteur(
    df_normalized: pd.DataFrame, df_acteur_from_db: pd.DataFrame
):
    if df_normalized.empty or df_acteur_from_db.empty:
        return df_normalized, df_acteur_from_db

    # Adding identifiant column to compare using identifiant_externe and source_code
    # instead of identifiant_unique (for the usecase of external_ids were updated)
    df_normalized["identifiant"] = df_normalized.apply(
        lambda row: compute_identifiant_unique(
            row["identifiant_externe"], row["source_code"]
        ),
        axis=1,
    )
    df_acteur_from_db["identifiant"] = df_acteur_from_db.apply(
        lambda row: compute_identifiant_unique(
            row["identifiant_externe"], row["source_code"]
        ),
        axis=1,
    )

    # find the duplicated identifiant in df_acteur_from_db and raise if any because
    # we can't resolve simply the mapping between source and db
    duplicates = df_acteur_from_db[
        df_acteur_from_db.duplicated("identifiant", keep=False)
    ]
    if not duplicates.empty:
        logger.warning(
            "Duplicated identifiant in df_acteur_from_db"
            f" {duplicates['identifiant'].tolist()}"
        )
        raise ValueError("Duplicated identifiant in df_acteur_from_db")

    # Replace identifiant_unique (from source) by identifiant (from db) for acteur
    # which doesn't have corelation between source, external_id and identifiant_unique
    df_normalized.set_index("identifiant", inplace=True)
    df_acteur_from_db.set_index("identifiant", inplace=True)
    df_normalized["identifiant_unique"] = df_normalized.index.map(
        lambda x: (
            df_acteur_from_db.loc[x, "identifiant_unique"]
            if x in df_acteur_from_db.index
            else df_normalized.loc[x, "identifiant_unique"]
        )
    )

    # Cleanup
    df_normalized.reset_index(inplace=True)
    df_acteur_from_db.reset_index(inplace=True)
    df_normalized.drop(columns=["identifiant"], inplace=True)
    df_acteur_from_db.drop(columns=["identifiant"], inplace=True)

    return df_normalized, df_acteur_from_db


def keep_acteur_changed(
    df_normalized: pd.DataFrame, df_acteur_from_db: pd.DataFrame, dag_config: DAGConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:

    from qfdmo.models import Acteur

    def remove_anonymized_acteur(
        df_acteur_from_db: pd.DataFrame, df_normalized: pd.DataFrame, metadata: dict
    ) -> (pd.DataFrame, pd.DataFrame, dict):
        anonymized_ids = set(
            df_acteur_from_db[df_acteur_from_db["nom"] == VALUE_ANONYMIZED][
                "identifiant_unique"
            ]
        ) & set(df_normalized["identifiant_unique"])

        if anonymized_ids:
            df_acteur_from_db = df_acteur_from_db[
                ~df_acteur_from_db["identifiant_unique"].isin(anonymized_ids)
            ]
            df_normalized = df_normalized[
                ~df_normalized["identifiant_unique"].isin(anonymized_ids)
            ]
            metadata[METADATA_ANONYMIZED_ACTEURS_IGNORED] = len(anonymized_ids)
        return df_acteur_from_db, df_normalized, metadata

    metadata = {}
    if df_acteur_from_db.empty:
        return df_normalized, df_acteur_from_db, metadata

    df_normalized, df_acteur_from_db = retrieve_identifiant_unique_from_existing_acteur(
        df_normalized, df_acteur_from_db
    )

    available_model_fields_to_compare = set(
        get_model_fields(Acteur, with_relationships=True, latlong=True)
    )

    columns_to_compare = (
        available_model_fields_to_compare & dag_config.get_expected_columns()
    )

    # Ignore acteurs anonymized because of RGPD
    df_acteur_from_db, df_normalized, metadata = remove_anonymized_acteur(
        df_acteur_from_db, df_normalized, metadata
    )

    # Préparer les dataframes pour la comparaison
    source_ids = set(df_normalized["identifiant_unique"])
    db_ids = set(df_acteur_from_db["identifiant_unique"])

    df_source = df_normalized[df_normalized["identifiant_unique"].isin(db_ids)]
    df_db = df_acteur_from_db[df_acteur_from_db["identifiant_unique"].isin(source_ids)]

    df_source = df_source.set_index("identifiant_unique")
    df_db = df_db.set_index("identifiant_unique")

    # Comparer les acteurs
    comparator = ActeurComparator(columns_to_compare)
    noupdate_ids = []

    for identifiant, row_source in df_source.iterrows():
        row_db = df_db.loc[identifiant]
        if not comparator.field_changed(row_source.to_dict(), row_db.to_dict()):
            noupdate_ids.append(identifiant)

    # Filtrer les dataframes
    df_normalized = df_normalized[
        ~df_normalized["identifiant_unique"].isin(noupdate_ids)
    ]
    df_acteur_from_db = df_acteur_from_db[
        ~df_acteur_from_db["identifiant_unique"].isin(noupdate_ids)
    ]

    # Préparer les métadonnées
    if comparator.metadata:
        metadata[METADATA_NUMBER_OF_UPDATES_BY_FIELD] = {" ": ["MODIF", "SUP", "AJOUT"]}
        for column, diff in comparator.metadata.items():
            metadata[METADATA_NUMBER_OF_UPDATES_BY_FIELD][column] = [
                diff.modif,
                diff.sup,
                diff.ajout,
            ]

    return df_normalized, df_acteur_from_db, metadata
