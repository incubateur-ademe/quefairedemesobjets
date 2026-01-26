import json
import logging

import pandas as pd
import requests
from cluster.config.metadata import (
    METADATA_DUPLICATES_FILTERED,
    METADATA_NO_SOUS_CATEGORIE_FILTERED,
    METADATA_SERVICE_DOMICILE_FILTERED,
)
from pydantic import BaseModel
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config.airflow_params import TRANSFORMATION_MAPPING
from sources.tasks.airflow_logic.config_management import (
    DAGConfig,
    NormalizationColumnDefault,
    NormalizationColumnRemove,
    NormalizationColumnRename,
    NormalizationColumnTransform,
    NormalizationDFTransform,
)
from sources.tasks.transform.exceptions import (
    ImportSourceException,
    ImportSourceValueWarning,
)
from sources.tasks.transform.transform_df import compute_location, merge_duplicates
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_fixed
from utils import logging_utils as log
from utils.django import django_setup_full

logger = logging.getLogger(__name__)

django_setup_full()

REPLACE_NULL_MAPPING = {
    key: ""
    for key in ["null", "none", "nan", "na", "n/a", "non applicable", "aucun", "-"]
}


class LogBase(BaseModel):
    fonction_de_transformation: str
    origine_colonnes: list[str]
    origine_valeurs: list[str]
    destination_colonnes: list[str]
    message: str


def _replace_null_insensitive(value):
    if isinstance(value, str) and value.strip().lower() in REPLACE_NULL_MAPPING:
        return ""
    if isinstance(value, list):
        return [v for v in value if v.strip().lower() not in REPLACE_NULL_MAPPING]
    return value


def _replace_explicit_null_values(df: pd.DataFrame) -> pd.DataFrame:
    return df.map(_replace_null_insensitive).replace({None: ""})


def get_transformation_function(function_name, dag_config):
    def transformation_function(row):
        return TRANSFORMATION_MAPPING[function_name](row, dag_config)

    return transformation_function


def _rename_columns(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    columns_to_rename = [
        t
        for t in dag_config.normalization_rules
        if isinstance(t, NormalizationColumnRename)
    ]
    for column_to_rename in columns_to_rename:
        logger.warning(
            f"Renaming columns from {column_to_rename.origin}"
            f" to {column_to_rename.destination}"
        )
        df.drop(columns=[column_to_rename.destination], inplace=True, errors="ignore")
        df = df.rename(
            columns={column_to_rename.origin: column_to_rename.destination},
        )
    return df


def _transform_columns(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    columns_to_transform = [
        t
        for t in dag_config.normalization_rules
        if isinstance(t, NormalizationColumnTransform)
    ]
    for column_to_transform in columns_to_transform:
        function_name = column_to_transform.transformation
        normalisation_function = get_transformation_function(function_name, dag_config)
        logger.warning(f"Transformation {function_name}")

        transformed_column = pd.Series(index=df.index, dtype="object")
        # Iterate over each row to apply the transformation
        for index, row in df.iterrows():
            origin_value = row[column_to_transform.origin]
            try:
                transformed_column[index] = normalisation_function(origin_value)
            except ImportSourceValueWarning as e:
                df.at[index, "log_warning"].append(
                    LogBase(
                        destination_colonnes=[column_to_transform.destination],
                        fonction_de_transformation=function_name,
                        origine_colonnes=[column_to_transform.origin],
                        origine_valeurs=[str(origin_value)],
                        message=str(e),
                    )
                )
                transformed_column[index] = ""
        df[column_to_transform.destination] = transformed_column

        if column_to_transform.origin not in dag_config.get_expected_columns():
            df.drop(columns=[column_to_transform.origin], inplace=True)
    return df


def _transform_df(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    columns_to_transform_df = [
        t
        for t in dag_config.normalization_rules
        if isinstance(t, NormalizationDFTransform)
    ]
    for column_to_transform_df in columns_to_transform_df:
        function_name = column_to_transform_df.transformation
        normalisation_function = get_transformation_function(function_name, dag_config)
        logger.warning(f"Transformation {function_name}")

        # Initialiser les colonnes de destination si elles n'existent pas
        for dest_col in column_to_transform_df.destination:
            if dest_col not in df.columns:
                df[dest_col] = ""

        for index, row in df.iterrows():
            # Récupérer les valeurs d'origine (peut être une ou plusieurs colonnes)
            origin_values = row[column_to_transform_df.origin]
            try:
                # La fonction de normalisation doit retourner un dict ou une liste
                # correspondant aux colonnes de destination
                result = normalisation_function(origin_values)

                # Assigner les résultats aux colonnes de destination
                if isinstance(result, pd.Series):
                    for i, dest_col in enumerate(column_to_transform_df.destination):
                        if i < len(result):
                            df.at[index, dest_col] = result.iloc[i]
                else:
                    raise ValueError(
                        f"Result of {function_name} should be pd.Series type,"
                        f" but it's {type(result)=}, {result=}"
                    )

            except ImportSourceException as e:
                log_column = "log_error" if e.is_blocking else "log_warning"
                df.at[index, log_column].append(
                    LogBase(
                        destination_colonnes=column_to_transform_df.destination,
                        fonction_de_transformation=function_name,
                        origine_colonnes=column_to_transform_df.origin,
                        origine_valeurs=[str(v) for v in origin_values.tolist()],
                        message=str(e),
                    )
                )
                # Définir des valeurs par défaut pour toutes les colonnes de destination
                for dest_col in column_to_transform_df.destination:
                    df.at[index, dest_col] = [] if dest_col.endswith("_codes") else ""

    return df


def _default_value_columns(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    columns_to_add_by_default = [
        t
        for t in dag_config.normalization_rules
        if isinstance(t, NormalizationColumnDefault)
    ]
    for column_to_add_by_default in columns_to_add_by_default:
        if isinstance(column_to_add_by_default.value, list):
            df[column_to_add_by_default.column] = [
                column_to_add_by_default.value
            ] * len(df)
        else:
            df[column_to_add_by_default.column] = column_to_add_by_default.value
    return df


def _remove_columns(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    columns_to_remove = [
        t.remove
        for t in dag_config.normalization_rules
        if isinstance(t, NormalizationColumnRemove) and t.remove in df.columns
    ]
    return df.drop(columns=columns_to_remove)


def _remove_undesired_lines(
    df: pd.DataFrame, dag_config: DAGConfig
) -> tuple[pd.DataFrame, dict]:
    metadata = {}

    # Compute metadata
    if "service_a_domicile" in df.columns:
        metadata[METADATA_SERVICE_DOMICILE_FILTERED] = str(
            (
                df["service_a_domicile"]
                .str.lower()
                .str.contains("service à domicile uniquement")
                .sum()
            )
            + (
                df["service_a_domicile"]
                .str.lower()
                .str.contains("oui exclusivement")
                .sum()
            )
        )

    if "sous_categorie_codes" in df.columns:
        if nb_empty_sous_categorie := len(
            df[df["sous_categorie_codes"].apply(len) == 0]
        ) + len(df[df["sous_categorie_codes"].isnull()]):
            metadata[METADATA_NO_SOUS_CATEGORIE_FILTERED] = str(nb_empty_sous_categorie)

    if all(
        column in df.columns
        for column in [
            "label_codes",
            "acteur_service_codes",
            "proposition_service_codes",
        ]
    ):
        df = merge_duplicates(
            df,
            group_column="identifiant_unique",
            merge_as_list_columns=["label_codes", "acteur_service_codes"],
            merge_as_proposition_service_columns=["proposition_service_codes"],
        )
    # Remove acteurs which propose only service à domicile
    if "service_a_domicile" in df.columns:
        df = df[df["service_a_domicile"].str.lower() != "oui exclusivement"]
        df = df[df["service_a_domicile"].str.lower() != "service à domicile uniquement"]

    # Remove acteurs which have no sous_categorie_codes
    if "sous_categorie_codes" in df.columns:
        df = df[df["sous_categorie_codes"].notnull()]
        df = df[df["sous_categorie_codes"].apply(len) > 0]

    # Find duplicates for logging
    dups = df[df["identifiant_unique"].duplicated(keep=False)]
    if not dups.empty:
        logger.warning(
            f"==== DOUBLONS SUR LES IDENTIFIANTS UNIQUES {len(dups) / 2} ====="
        )
        log.preview("Doublons sur identifiant_unique", dups)
        metadata[METADATA_DUPLICATES_FILTERED] = str(len(dups) / 2)

    return df, metadata


def _display_warning_about_missing_location(df: pd.DataFrame) -> None:
    # TODO: A voir ce qu'on doit faire de ces acteurs non digitaux mais sans
    # localisation (proposition : les afficher en erreur directement ?)
    if "location" in df.columns and "acteur_type_code" in df.columns:
        df_acteur_sans_loc = df[
            (df["location"].isnull()) & (df["acteur_type_code"] != "acteur_digital")
        ]
        if not df_acteur_sans_loc.empty:
            nb_acteurs = len(df)
            logger.warning(
                f"Nombre d'acteurs sans localisation: {len(df_acteur_sans_loc)} / "
                f"{nb_acteurs}"
            )
            log.preview("Acteurs sans localisation", df_acteur_sans_loc)


def _manage_oca_config(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    if dag_config.oca_deduplication_source:
        df = df.assign(source_code=df["source_code"].str.split("|")).explode(
            "source_code"
        )
    if oca_prefix := dag_config.oca_prefix:
        df["source_code"] = df["source_code"].apply(
            lambda x: oca_prefix + "_" + x.strip().lower()
        )
    # Recalcul de l'identifiant unique
    normalisation_function = get_transformation_function(
        "clean_identifiant_unique", dag_config
    )
    df[["identifiant_unique"]] = df[["identifiant_externe", "source_code"]].apply(
        normalisation_function, axis=1
    )
    return df


def source_data_normalize(
    df_acteur_from_source: pd.DataFrame,
    dag_config: DAGConfig,
    dag_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """
    Normalisation des données source. Passée cette étape:
    - toutes les sources doivent avoir une nomenclature et formatage alignés
    - les sources peuvent préservées des spécificités (ex: présence/absence de SIRET)
        mais toujours en cohérence avec les règles de nommage et formatage
    - Ajout des colonnes avec valeurs par défaut
    """

    df = df_acteur_from_source

    if dag_id == "pharmacies":
        # Patch pour les pharmacies car l'apostrophe n'est pas bien géré dans la
        # configuration de airflow
        df.rename(
            columns={"Numéro d'établissement": "identifiant_externe"},
            inplace=True,
        )

    # Init log_warning for each row
    df["log_warning"] = [[] for _ in range(len(df))]
    df["log_error"] = [[] for _ in range(len(df))]

    df = _replace_explicit_null_values(df)

    df = _rename_columns(df, dag_config)
    log.preview("df after renaming columns", df)
    df = _transform_columns(df, dag_config)
    log.preview("df after transforming columns", df)
    df = _default_value_columns(df, dag_config)
    log.preview("df after adding default value columns", df)
    df = _transform_df(df, dag_config)
    log.preview("df after transforming df", df)
    df = _remove_columns(df, dag_config)
    log.preview("df after removing columns", df)

    # extract logs by identifiant_unique
    df_log_error = df[["identifiant_unique", "log_error"]]
    df_log_warning = df[["identifiant_unique", "log_warning"]]

    df_log_error = df_log_error[df_log_error["log_error"].apply(len) > 0]
    df_log_warning = df_log_warning[df_log_warning["log_warning"].apply(len) > 0]

    # flatten df_log_error and df_log_warning
    df_log_error = df_log_error.explode("log_error")
    df_log_warning = df_log_warning.explode("log_warning")
    log.preview("df_log_error", df_log_error)
    # Transform LogBase objects into separate columns
    if not df_log_error.empty:
        df_log_error_expanded = pd.json_normalize(
            df_log_error["log_error"].apply(lambda x: x.dict() if x else {})
        )
        df_log_error = pd.concat(
            [
                df_log_error[["identifiant_unique"]].reset_index(drop=True),
                df_log_error_expanded.reset_index(drop=True),
            ],
            axis=1,
        )
    log.preview("df_log_error", df_log_error)

    if not df_log_warning.empty:
        df_log_warning_expanded = pd.json_normalize(
            df_log_warning["log_warning"].apply(lambda x: x.dict() if x else {})
        )
        df_log_warning = pd.concat(
            [
                df_log_warning[["identifiant_unique"]].reset_index(drop=True),
                df_log_warning_expanded.reset_index(drop=True),
            ],
            axis=1,
        )

    # drop row with not empty log_error
    df = df[df["log_error"].apply(len) == 0]

    # drop logs from df
    df = df.drop(columns=["log_error"])
    df = df.drop(columns=["log_warning"])

    # Merge and delete undesired lines
    df, metadata = _remove_undesired_lines(df, dag_config)
    log.preview("df after removing undesired lines", df)

    # deduplication_on_source_code
    if dag_config.is_oca:
        df = _manage_oca_config(df, dag_config)

    # Check that the dataframe has the expected columns
    expected_columns = dag_config.get_expected_columns()

    if set(df.columns) != expected_columns:
        raise ValueError(
            f"""Le dataframe normalisé (données sources) n'a pas les colonnes attendues.
            Colonnes en trop: {set(df.columns) - expected_columns}
            Colonnes manquantes: {expected_columns - set(df.columns)}"""
        )

    # Etapes de normalisation spécifiques aux sources
    if dag_id == "pharmacies":
        df = df_normalize_pharmacie(df)

    if dag_id == "source_sinoe":
        df = df_normalize_sinoe(df)

    # Log si des localisations sont manquantes parmis les acteurs non digitaux
    _display_warning_about_missing_location(df)

    log.preview("df après normalisation", df)
    if df.empty:
        raise ValueError("Plus aucune donnée disponible après normalisation")
    return df, df_log_error, df_log_warning, metadata


def df_normalize_pharmacie(df: pd.DataFrame) -> pd.DataFrame:
    # FIXME : à déplacer dans une fonction df ?
    # controle des adresses et localisation des pharmacies
    df = df.apply(enrich_from_ban_api, axis=1)
    # On supprime les pharmacies sans localisation
    nb_pharmacies_sans_loc = len(df[(df["latitude"] == 0) | (df["longitude"] == 0)])
    nb_pharmacies = len(df)
    logger.warning(
        f"Nombre de pharmacies sans localisation: {nb_pharmacies_sans_loc}"
        f" / {nb_pharmacies}"
    )
    df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]
    return df


def df_normalize_sinoe(
    df: pd.DataFrame,
) -> pd.DataFrame:
    # DOUBLONS: extra sécurité: même si on ne devrait pas obtenir
    # de doublon grâce à l'API (q_mode=simple&ANNEE_eq=2025)
    # on vérifie qu'on a qu'une année
    log.preview("ANNEE uniques", df["ANNEE"].unique().tolist())
    if df["ANNEE"].nunique() != 1:
        raise ValueError("Plusieurs ANNEE, changer requête API pour n'en avoir qu'une")
    df = df.drop(columns=["ANNEE"])

    return df


@retry(wait=wait_fixed(5), stop=stop_after_attempt(5))
def enrich_from_ban_api(row: pd.Series) -> pd.Series:
    engine = PostgresConnectionManager().engine

    adresse = row["adresse"] if row["adresse"] else ""
    code_postal = row["code_postal"] if row["code_postal"] else ""
    ville = row["ville"] if row["ville"] else ""

    ban_cache_row = engine.execute(
        text(
            "SELECT * FROM data_bancache WHERE adresse = :adresse and code_postal = "
            ":code_postal and ville = :ville and modifie_le > now() - interval '30 day'"
            " order by modifie_le desc limit 1"
        ),
        adresse=adresse,
        code_postal=str(code_postal),
        ville=ville,
    ).fetchone()

    if ban_cache_row:
        result = ban_cache_row["ban_returned"]
    else:
        ban_adresse = _compute_ban_adresse(row)
        url = "https://data.geopf.fr/geocodage/search/"
        r = requests.get(url, params={"q": ban_adresse})
        if r.status_code != 200:
            raise Exception(f"Failed to get data from API: {r.status_code}")
        result = r.json()
        engine.execute(
            text(
                "INSERT INTO data_bancache"
                " (adresse, code_postal, ville, ban_returned, modifie_le)"
                " VALUES (:adresse, :code_postal, :ville, :result, NOW())"
            ),
            adresse=adresse,
            code_postal=code_postal,
            ville=ville,
            result=json.dumps(result),
        )

    better_result = None
    better_geo = None
    if "features" in result and result["features"]:
        better_geo = result["features"][0]["geometry"]["coordinates"]
        better_result = result["features"][0]["properties"]
    if better_geo and better_result and better_result["score"] > 0.5:
        better_postcode = (
            better_result["postcode"]
            if "postcode" in better_result
            else row["code_postal"]
        )
        better_city = better_result["city"] if "city" in better_result else row["ville"]
        better_adresse = (
            better_result["name"] if "name" in better_result else row["adresse"]
        )
        row["longitude"] = better_geo[0]
        row["latitude"] = better_geo[1]
        row["adresse"] = better_adresse
        row["code_postal"] = better_postcode
        row["ville"] = better_city
    else:
        row["longitude"] = 0
        row["latitude"] = 0

    row["location"] = compute_location(row[["latitude", "longitude"]], None)
    return row


def _compute_ban_adresse(row):
    ban_adresse = [row["adresse"], row["code_postal"], row["ville"]]
    ban_adresse = [str(x) for x in ban_adresse if x]
    return " ".join(ban_adresse)
