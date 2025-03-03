import logging
from dataclasses import dataclass

import pandas as pd
from sources.tasks.airflow_logic.config_management import DAGConfig
from utils.django import django_setup_full, get_model_fields

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

    def _compare_lists(self, source: list, db: list) -> bool:
        return sorted(source) != sorted(db)

    def _compare_proposition_services(self, source: list[dict], db: list[dict]) -> bool:
        source_sorted = sorted(source, key=lambda x: x["action"])
        db_sorted = sorted(db, key=lambda x: x["action"])

        for item in source_sorted:
            item["sous_categories"] = sorted(item["sous_categories"])
        for item in db_sorted:
            item["sous_categories"] = sorted(item["sous_categories"])

        return source_sorted != db_sorted

    def _get_diff_type(self, source_val, db_val) -> list[int]:
        if not source_val:
            return [0, 1, 0]  # SUP
        if not db_val:
            return [0, 0, 1]  # AJOUT
        return [1, 0, 0]  # MODIF

    def compare_rows(self, row_source: dict, row_db: dict) -> dict[str, list[int]]:
        columns_updated = {}
        for column in self.columns_to_compare:
            source_val = row_source[column]
            db_val = row_db[column]

            is_updated = False
            if column == "proposition_service_codes":
                is_updated = self._compare_proposition_services(source_val, db_val)
            elif isinstance(source_val, list) and isinstance(db_val, list):
                is_updated = self._compare_lists(source_val, db_val)
            else:
                is_updated = source_val != db_val

            if is_updated:
                columns_updated[column] = self._get_diff_type(source_val, db_val)
                if column not in self.metadata:
                    self.metadata[column] = ColumnDiff()
                self.metadata[column].add(columns_updated[column])

        return columns_updated


def keep_acteur_changed(
    df_normalized: pd.DataFrame, df_acteur_from_db: pd.DataFrame, dag_config: DAGConfig
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:

    from qfdmo.models import Acteur

    metadata = {}
    if df_acteur_from_db.empty:
        return df_normalized, df_acteur_from_db, metadata

    available_model_fields_to_compare = set(
        get_model_fields(Acteur, with_relationships=True, latlong=True)
    )

    columns_to_compare = (
        available_model_fields_to_compare & dag_config.get_expected_columns()
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
        if not comparator.compare_rows(row_source.to_dict(), row_db.to_dict()):
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
        metadata = {"Nombre de mise à jour par champ": {" ": ["MODIF", "SUP", "AJOUT"]}}
        for column, diff in comparator.metadata.items():
            metadata["Nombre de mise à jour par champ"][column] = [
                diff.modif,
                diff.sup,
                diff.ajout,
            ]

    return df_normalized, df_acteur_from_db, metadata
