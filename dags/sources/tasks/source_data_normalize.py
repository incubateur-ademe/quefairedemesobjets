import logging

import pandas as pd
from utils import logging_utils as log
from utils import mapping_utils
from utils import shared_constants as constants

logger = logging.getLogger(__name__)


def df_normalize_sinoe(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Normalisation spécifique à la dataframe SINOE"""

    product_mapping = params["product_mapping"]
    dechet_mapping = params["dechet_mapping"]
    public_mapping = {
        "DMA/PRO": constants.PUBLIC_PRO_ET_PAR,
        "DMA": constants.PUBLIC_PAR,
        "PRO": constants.PUBLIC_PRO,
        "NP": None,
    }
    # IDENTIFIANTS:
    df["identifiant_externe"] = df["identifiant_externe"].astype(str).str.strip()

    # MISC
    df["acteur_type_id"] = 7
    # df["ecoorganisme"] = source_code
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
    logger.info(f"# déchetteries avant logique produitsdechets_acceptes: {len(df)}")
    col = "produitsdechets_acceptes"

    # on supprime les déchetteries qu'on peut pas categoriser
    df = df[df[col].notnull()]

    # on cinde les codes déchêts en liste (ex: "01.3|02.31" -> ["01.3", "02.31"])
    df[col] = df[col].str.split("|")

    # nettoyage après cindage
    df[col] = df[col].apply(
        # "NP": "Non précisé", on garde pas
        lambda x: [v.strip() for v in x if v.strip() not in ("", "nan", "NP")]
    )
    # On map à des chaîne de caractères (ex: "01" -> "Déchets de composés chimiques")
    # en ignorant les codes déchets qui ne sont pas dans notre product_mapping
    df[col] = df[col].apply(
        lambda x: [dechet_mapping[v] for v in x if dechet_mapping[v] in product_mapping]
    )
    # Encore une fois on supprime les déchetteries qu'on peut pas categoriser
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


def source_data_normalize(**kwargs):
    """Normalisation des données source. Passée cette étape:
    - toutes les sources doivent avoir une nomenclature et formatage alignés
    - les sources peuvent préservées des spécificités (ex: présence/absence de SIRET)
        mais toujours en cohérence avec les règles de nommage et formatage
    """
    df = kwargs["ti"].xcom_pull(task_ids="source_data_download")
    log.preview("df avant normalisation", df)

    params = kwargs["params"]
    source_code = params.get("source_code")
    column_mapping = params.get("column_mapping", {})

    # Renommage des colonnes
    df = df.rename(columns={k: v for k, v in column_mapping.items() if v is not None})

    # Vérification requise pour la gestion source/ecoorganisme
    if source_code is None and "ecoorganisme" not in df.columns:
        raise ValueError("Pas de 'source_code' et pas de colonne 'ecoorganisme'")

    # Etapes de normalisation spécifiques aux sources
    if source_code == "ADEME_SINOE_Decheteries":
        df = df_normalize_sinoe(df, params)

    # Formattage des types
    # TODO: on dévrait pouvoir utiliser les modèles django/DB pour automatiser cela
    df["identifiant_externe"] = df["identifiant_externe"].astype(str)
    df["identifiant_unique"] = df.apply(
        lambda x: mapping_utils.create_identifiant_unique(x, source_name=source_code),
        axis=1,
    )

    # Règle métier: Ne pas ingérer les acteurs avec public pur PRO
    df = df[df["public_accueilli"] != constants.PUBLIC_PRO]

    # Suppresion des colonnes non voulues:
    # - mappées à None
    # - commençant par _ (internes aux sources)
    # - TODO: dropper ce que notre modèle django ne peut pas gérer
    df = df.drop(columns=[k for k, v in column_mapping.items() if v is None])
    df = df.drop(columns=[col for col in df.columns if col.startswith("_")])

    log.preview("df après normalisation", df)
    if df.empty:
        raise ValueError("Plus aucune donnée disponible après normalisation")
    return df
