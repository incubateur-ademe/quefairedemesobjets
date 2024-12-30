import json
import logging

import pandas as pd
import requests
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config import shared_constants as constants
from sources.config.airflow_params import TRANSFORMATION_MAPPING
from sources.tasks.airflow_logic.config_management import (
    DAGConfig,
    NormalizationColumnDefault,
    NormalizationColumnRemove,
    NormalizationColumnRename,
    NormalizationColumnTransform,
    NormalizationDFTransform,
)
from sources.tasks.transform.transform_df import merge_duplicates
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_fixed
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def get_transformation_function(function_name, dag_config):
    def transformation_function(row):
        return TRANSFORMATION_MAPPING[function_name](row, dag_config)

    return transformation_function


def _rename_columns(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    columns_to_rename = [
        t
        for t in dag_config.column_transformations
        if isinstance(t, NormalizationColumnRename)
    ]
    return df.rename(
        columns={
            column_to_rename.origin: column_to_rename.destination
            for column_to_rename in columns_to_rename
        },
    )


def _transform_columns(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    columns_to_transform = [
        t
        for t in dag_config.column_transformations
        if isinstance(t, NormalizationColumnTransform)
    ]
    for column_to_transform in columns_to_transform:
        function_name = column_to_transform.transformation
        normalisation_function = get_transformation_function(function_name, dag_config)
        logger.warning(f"Transformation {function_name}")
        df[column_to_transform.destination] = df[column_to_transform.origin].apply(
            normalisation_function
        )
        if column_to_transform.destination != column_to_transform.origin:
            df.drop(columns=[column_to_transform.origin], inplace=True)
    return df


def _transform_df(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    columns_to_transform_df = [
        t
        for t in dag_config.column_transformations
        if isinstance(t, NormalizationDFTransform)
    ]
    for column_to_transform_df in columns_to_transform_df:
        function_name = column_to_transform_df.transformation
        normalisation_function = get_transformation_function(function_name, dag_config)

        logger.warning(f"Transformation {function_name}")
        df[column_to_transform_df.destination] = df[
            column_to_transform_df.origin
        ].apply(normalisation_function, axis=1)
        # FIXME: Pour le moment, on ne souhaite pas supprimer les colonnes
        #  columns_to_drop = [
        #     column_origin
        #     for column_origin in column_to_transform_df.origin
        #     if column_origin not in column_to_transform_df.destination
        # ]
        # df.drop(columns=columns_to_drop, inplace=True)
    return df


def _default_value_columns(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    columns_to_add_by_default = [
        t
        for t in dag_config.column_transformations
        if isinstance(t, NormalizationColumnDefault)
    ]
    for column_to_add_by_default in columns_to_add_by_default:
        df[column_to_add_by_default.column] = column_to_add_by_default.value
    return df


def _remove_columns(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    columns_to_remove = [
        t.remove
        for t in dag_config.column_transformations
        if isinstance(t, NormalizationColumnRemove)
    ]
    return df.drop(columns=columns_to_remove)


def _remove_undesired_lines(df: pd.DataFrame, dag_config: DAGConfig) -> pd.DataFrame:
    if dag_config.merge_duplicated_acteurs:
        df = merge_duplicates(
            df,
            group_column="identifiant_unique",
            merge_column="produitsdechets_acceptes",
        )

    # Suppression des lignes dont public_acceuilli est uniqueùent les professionnels
    df = df[df["public_accueilli"] != constants.PUBLIC_PRO]

    # Après les appels aux fonctions de normalisation spécifiques aux sources
    # On supprime les acteurs qui n'ont pas de produits acceptés
    df = df[df["souscategorie_codes"].notnull()]
    df = df[df["souscategorie_codes"].apply(len) > 0]

    # Trouver les doublons pour les publier dans les logs
    dups = df[df["identifiant_unique"].duplicated(keep=False)]
    if not dups.empty:
        logger.warning(
            f"==== DOUBLONS SUR LES IDENTIFIANTS UNIQUES {len(dups)/2} ====="
        )
        log.preview("Doublons sur identifiant_unique", dups)
    if dag_config.ignore_duplicates:
        # TODO: Attention aux lignes dupliquées à cause de de service en ligne
        #  + physique
        df = df.drop_duplicates(subset=["identifiant_unique"], keep="first")

    return df


def source_data_normalize(
    df_acteur_from_source: pd.DataFrame,
    dag_config: DAGConfig,
    dag_id: str,
) -> pd.DataFrame:
    """
    Normalisation des données source. Passée cette étape:
    - toutes les sources doivent avoir une nomenclature et formatage alignés
    - les sources peuvent préservées des spécificités (ex: présence/absence de SIRET)
        mais toujours en cohérence avec les règles de nommage et formatage
    - Ajout des colonnes avec valeurs par défaut
    """
    df = df_acteur_from_source
    df = _rename_columns(df, dag_config)
    df = _transform_columns(df, dag_config)
    df = _default_value_columns(df, dag_config)
    df = _transform_df(df, dag_config)
    df = _remove_columns(df, dag_config)

    # Vérification que le dataframe a exactement les colonnes attendues
    expected_columns = dag_config.get_expected_columns()

    if set(df.columns) != expected_columns:
        raise ValueError(
            "Le dataframe n'a pas les colonnes attendues: "
            f"{set(df.columns)} != {expected_columns}"
        )

    # Etapes de normalisation spécifiques aux sources
    # TODO: Remplacer par le dag_id
    if dag_id == "pharmacies":
        df = df_normalize_pharmacie(df)

    # TODO: Remplacer par le dag_id
    if dag_id == "sinoe":
        df = df_normalize_sinoe(
            df,
            product_mapping=dag_config.product_mapping,
            dechet_mapping=dag_config.dechet_mapping,
        )

    # Merge et suppression des lignes indésirables
    df = _remove_undesired_lines(df, dag_config)

    log.preview("df après normalisation", df)
    if df.empty:
        raise ValueError("Plus aucune donnée disponible après normalisation")
    return df

    # # TODO: Je n'ai pas vu la source qui applique cette règle
    # if "statut" in df.columns:
    #     df["statut"] = df["statut"].map(
    #         {
    #             1: constants.ACTEUR_ACTIF,
    #             0: constants.ACTEUR_SUPPRIME,
    #             constants.ACTEUR_ACTIF: constants.ACTEUR_ACTIF,
    #             "INACTIF": constants.ACTEUR_INACTIF,
    #             "SUPPRIME": constants.ACTEUR_SUPPRIME,
    #         }
    #     )
    #     df["statut"] = df["statut"].fillna(constants.ACTEUR_ACTIF)
    # else:
    #     df["statut"] = constants.ACTEUR_ACTIF


def df_normalize_pharmacie(df: pd.DataFrame) -> pd.DataFrame:
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
    product_mapping: dict,
    dechet_mapping: dict,
) -> pd.DataFrame:
    """Normalisation spécifique à la dataframe SINOE"""

    public_mapping = {
        "DMA/PRO": constants.PUBLIC_PRO_ET_PAR,
        "DMA": constants.PUBLIC_PAR,
        "PRO": constants.PUBLIC_PRO,
        "NP": None,
    }

    # Pour forcer l'action "trier"
    df["point_de_collecte_ou_de_reprise_des_dechets"] = True
    df["public_accueilli"] = df["public_accueilli"].map(public_mapping)

    # DOUBLONS: extra sécurité: même si on ne devrait pas obtenir
    # de doublon grâce à l'API (q_mode=simple&ANNEE_eq=2024)
    # on vérifie qu'on a qu'une année
    log.preview("ANNEE uniques", df["ANNEE"].unique().tolist())
    if df["ANNEE"].nunique() != 1:
        raise ValueError("Plusieurs ANNEE, changer requête API pour n'en avoir qu'une")
    df = df.drop(columns=["ANNEE"])

    # GEO
    df["_geopoint"] = df["_geopoint"].str.split(",")
    df["latitude"] = df["_geopoint"].map(lambda x: x[0].strip()).astype(float)
    df["longitude"] = df["_geopoint"].map(lambda x: x[1].strip()).astype(float)
    df = df.drop(columns=["_geopoint"])

    # PRODUCT MAPPING:
    # TODO: à sortir dans une fonction df pour tester/débugger plus facilement
    logger.info(f"# déchetteries avant logique produitsdechets_acceptes: {len(df)}")
    col = "produitsdechets_acceptes"

    # on supprime les déchetteries qu'on peut pas categoriser
    df = df[df[col].notnull()]

    # on cinde les codes déchêts en liste (ex: "01.3|02.31" -> ["01.3", "02.31"])
    df[col] = df[col].str.split("|")

    # nettoyage après cindage
    df[col] = df[col].apply(
        # "NP": "Non précisé", on garde pas
        lambda x: [v.strip() for v in x if v.strip().lower() not in ("", "nan", "np")]
    )
    # On map à des chaîne de caractères (ex: "01" -> "Déchets de composés chimiques")
    # en ignorant les codes déchets qui ne sont pas dans notre product_mapping
    df[col] = df[col].apply(
        lambda x: [dechet_mapping[v] for v in x if dechet_mapping[v] in product_mapping]
    )
    # Encore une fois on supprime les déchetteries qu'on ne peut pas categoriser
    df = df[df[col].apply(len) > 0]
    logger.info(f"# déchetteries après logique produitsdechets_acceptes: {len(df)}")
    souscats_dechet = set(df[col].explode())
    souscats_mapping = set(product_mapping.keys())
    souscats_invalid = souscats_dechet - souscats_mapping
    log.preview("Sous-catégories du dechet_mapping", souscats_dechet)
    log.preview("Sous-catégories du product_mapping", souscats_mapping)
    if souscats_invalid:
        raise ValueError(f"Sous-catégories invalides: {souscats_invalid}")

    return df


@retry(wait=wait_fixed(5), stop=stop_after_attempt(5))
def enrich_from_ban_api(row: pd.Series) -> pd.Series:
    engine = PostgresConnectionManager().engine

    adresse = row["adresse"] if row["adresse"] else ""
    code_postal = row["code_postal"] if row["code_postal"] else ""
    ville = row["ville"] if row["ville"] else ""

    ban_cache_row = engine.execute(
        text(
            "SELECT * FROM qfdmo_bancache WHERE adresse = :adresse and code_postal = "
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
        url = "https://api-adresse.data.gouv.fr/search/"
        r = requests.get(url, params={"q": ban_adresse})
        if r.status_code != 200:
            raise Exception(f"Failed to get data from API: {r.status_code}")
        result = r.json()
        engine.execute(
            text(
                "INSERT INTO qfdmo_bancache"
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
    return row


def _compute_ban_adresse(row):
    ban_adresse = [row["adresse"], row["code_postal"], row["ville"]]
    ban_adresse = [str(x) for x in ban_adresse if x]
    return " ".join(ban_adresse)
