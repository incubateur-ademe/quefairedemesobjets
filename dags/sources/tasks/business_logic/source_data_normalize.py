import json
import logging
from typing import List

import pandas as pd
import requests
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config import shared_constants as constants
from sources.config.airflow_params import TRANSFORMATION_MAPPING
from sources.tasks.transform.transform_column import (
    cast_eo_boolean_or_string_to_boolean,
    mapping_try_or_fallback_column_value,
)
from sources.tasks.transform.transform_df import merge_duplicates
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_fixed
from utils import logging_utils as log
from utils import mapping_utils
from utils.base_utils import extract_details, get_address

logger = logging.getLogger(__name__)


def source_data_normalize(
    df_acteur_from_source: pd.DataFrame,
    source_code: str | None,
    column_mapping: dict,
    column_transformations: List[dict],
    columns_to_add_by_default: dict,
    label_bonus_reparation: str | None,
    validate_address_with_ban: bool,
    ignore_duplicates: bool,
    combine_columns_categories: list,
    merge_duplicated_acteurs: bool,
    product_mapping: dict,
    dechet_mapping: dict,
    acteurtype_id_by_code: dict,
    source_id_by_code: dict,
) -> pd.DataFrame:
    """
    Normalisation des données source. Passée cette étape:
    - toutes les sources doivent avoir une nomenclature et formatage alignés
    - les sources peuvent préservées des spécificités (ex: présence/absence de SIRET)
        mais toujours en cohérence avec les règles de nommage et formatage
    - Ajout des colonnes avec valeurs par défaut
    """
    df = df_acteur_from_source

    # Renommage des colonnes
    df = df.rename(columns={k: v for k, v in column_mapping.items() if v is not None})

    # Transformation des colonnes
    # Appliquer la transformation à la colonne d'origine et stocker le résultat
    # dans la colonne de destination
    for transformation in column_transformations:
        function_name = transformation["transformation"]
        df[transformation["destination"]] = df[transformation["origin"]].apply(
            TRANSFORMATION_MAPPING[function_name]
        )
        if transformation["destination"] != transformation["origin"]:
            df.drop(columns=[transformation["origin"]], inplace=True)

    # DEBUT Traitement des identifiants

    # Identifiant externe
    if "identifiant_externe" in df.columns:
        # TODO: simplifier cette partie de code quite à faire des migrations
        count_nan = df["identifiant_externe"].isna().sum()
        if count_nan > 0:
            logger.warning(f"Nombre de NaN dans 'identifiant_externe': {count_nan}")
        # TODO : A voir si on dégage ceux qui n'ont pas d'identifiant externe
        # cf. Christian
        if "nom_de_lorganisme" in df.columns:
            df["identifiant_externe"] = df["identifiant_externe"].fillna(
                df["nom_de_lorganisme"]
                .str.replace("-", "")
                .str.replace(" ", "_")
                .str.replace("__", "_")
            )
        df["identifiant_externe"] = df["identifiant_externe"].astype(str)
    else:
        raise ValueError("Pas de colonne 'identifiant_externe'")

    # Source : nécessaire pour les identifiants uniques
    # TODO : un peu crado, à revoir
    # A cause de la résolution de l'identifiant unique qui dépend du code de la source
    if "source_id" in df.columns:
        df["source_code"] = df["source_id"]
        df["source_id"] = df["source_id"].map(source_id_by_code)
    elif source_code is not None:
        df["source_code"] = source_code
        df["source_id"] = source_id_by_code[source_code]
    else:
        ValueError("Pas de colonne 'source_id'")

    # Identifiant unique
    # TODO: on dévrait pouvoir utiliser les modèles django/DB pour automatiser cela
    df["identifiant_unique"] = df.apply(
        lambda x: mapping_utils.create_identifiant_unique(x),
        axis=1,
    )

    # FIN Traitement des identifiants

    if combine_columns_categories:
        df["produitsdechets_acceptes"] = df.apply(
            lambda row: mapping_utils.combine_categories(
                row, combine_columns_categories
            ),
            axis=1,
        )

    # Après le traitement des identifiants :
    # Merge les lignes au plus tôt pour minimiser le traitement (réduction de la taille
    # du df)
    if merge_duplicated_acteurs:
        df = merge_duplicates(
            df,
            group_column="identifiant_unique",
            merge_column="produitsdechets_acceptes",
        )

    for k, val in columns_to_add_by_default.items():
        df[k] = val

    # Avant le renommage des colonnes prise en chage de adresse_format_ban
    if "adresse_format_ban" in df.columns:
        if validate_address_with_ban:
            df[["adresse", "code_postal", "ville"]] = df.apply(get_address, axis=1)
        else:
            df[["adresse", "code_postal", "ville"]] = df.apply(extract_details, axis=1)

    if "statut" in df.columns:
        df["statut"] = df["statut"].map(
            {
                1: constants.ACTEUR_ACTIF,
                0: constants.ACTEUR_SUPPRIME,
                constants.ACTEUR_ACTIF: constants.ACTEUR_ACTIF,
                "INACTIF": constants.ACTEUR_INACTIF,
                "SUPPRIME": constants.ACTEUR_SUPPRIME,
            }
        )
        df["statut"] = df["statut"].fillna(constants.ACTEUR_ACTIF)
    else:
        df["statut"] = constants.ACTEUR_ACTIF

    if "public_accueilli" in df.columns:

        df["public_accueilli"] = mapping_try_or_fallback_column_value(
            df["public_accueilli"],
            {
                "particuliers et professionnels": constants.PUBLIC_PRO_ET_PAR,
                "professionnels": constants.PUBLIC_PRO,
                "particuliers": constants.PUBLIC_PAR,
                "aucun": constants.PUBLIC_AUCUN,
            },
        )

        # Règle métier: Ne pas ingérer les acteurs avec public pur PRO
        df = df[df["public_accueilli"] != constants.PUBLIC_PRO]

    for column in ["uniquement_sur_rdv", "exclusivite_de_reprisereparation"]:
        if column in df.columns:

            df[column] = df[column].apply(cast_eo_boolean_or_string_to_boolean)

    if "reprise" in df.columns:

        df["reprise"] = mapping_try_or_fallback_column_value(
            df["reprise"],
            {
                "1 pour 0": constants.REPRISE_1POUR0,
                "1 pour 1": constants.REPRISE_1POUR1,
                "non": constants.REPRISE_1POUR0,
                "oui": constants.REPRISE_1POUR1,
            },
        )

    if "labels_etou_bonus" in df.columns and label_bonus_reparation:
        df["labels_etou_bonus"] = df["labels_etou_bonus"].str.replace(
            "Agréé Bonus Réparation", label_bonus_reparation
        )
    if "url" in df.columns:
        df["url"] = df["url"].map(mapping_utils.prefix_url)

    # Etapes de normalisation spécifiques aux sources
    if source_code == "ordredespharmaciens":
        df = df_normalize_pharmacie(df)

    if source_code == "ADEME_SINOE_Decheteries":
        df = df_normalize_sinoe(
            df,
            product_mapping=product_mapping,
            dechet_mapping=dechet_mapping,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )
    else:
        df["acteur_type_id"] = df["acteur_type_id"].apply(
            lambda x: mapping_utils.transform_acteur_type_id(
                x, acteurtype_id_by_code=acteurtype_id_by_code
            )
        )

    # Suppresion des colonnes non voulues:
    # - mappées à None
    # - commençant par _ (internes aux sources)
    # - TODO: dropper ce que notre modèle django ne peut pas gérer
    df = df.drop(columns=[k for k, v in column_mapping.items() if v is None])
    df = df.drop(columns=[col for col in df.columns if col.startswith("_")])

    # Trouver les doublons pour les publier dans les logs
    dups = df[df["identifiant_unique"].duplicated(keep=False)]
    if not dups.empty:
        logger.warning(
            f"==== DOUBLONS SUR LES IDENTIFIANTS UNIQUES {len(dups)/2} ====="
        )
        log.preview("Doublons sur identifiant_unique", dups)
    if ignore_duplicates:
        # TODO: Attention aux lignes dupliquées à cause de de service en ligne
        #  + physique
        df = df.drop_duplicates(subset=["identifiant_unique"], keep="first")

    # Après les appels aux fonctions de normalisation spécifiques aux sources
    # On supprime les acteurs qui n'ont pas de produits acceptés
    df = df[df["produitsdechets_acceptes"].notnull()]
    df = df[df["produitsdechets_acceptes"].apply(len) > 0]

    log.preview("df après normalisation", df)
    if df.empty:
        raise ValueError("Plus aucune donnée disponible après normalisation")
    return df


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
    acteurtype_id_by_code: dict,
) -> pd.DataFrame:
    """Normalisation spécifique à la dataframe SINOE"""

    public_mapping = {
        "DMA/PRO": constants.PUBLIC_PRO_ET_PAR,
        "DMA": constants.PUBLIC_PAR,
        "PRO": constants.PUBLIC_PRO,
        "NP": None,
    }

    # MISC
    df["acteur_type_id"] = acteurtype_id_by_code["decheterie"]  # Déchetterie
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
