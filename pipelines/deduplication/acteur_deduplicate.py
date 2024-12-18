"""
Script pour dédupliquer les acteurs:

Paramètres requis:
 - DB_URL_{ENVIRONNEMENT}: connexion base de données
 - CLUSTERING_CSV_FILEPATH: fichier CSV d'entrée
    avec 1 ligne = cluster_id -> identifiant_unique

Paramètres optionnelles:
 - CLUSTER_IDS_TO_CHANGES: pour tester un cluster en particulier
 - DRY_RUN: pour tester sans modifier la DB

Execution:
 - python acteur_deduplicate.py

Nommage des variables:
 - suffixe "_src" pour la donnée de source
 - suffixe "_db" pour la donnée en base de données
"""

import json
import os
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from models.change import Change
from rich import print
from rich.prompt import Confirm, Prompt
from rich.traceback import install
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from tasks.db_manage_cluster import db_manage_cluster
from tasks.source_data_get import source_data_get
from tests.verifications import CLUSTER_IDS_TO_CHANGES
from transforms.dataframes import df_mapping_one_to_many
from utils.cli import banner

install()  # you can install globally to your env, see docs

# ------------------------------------------
# PARAMETERS
# ------------------------------------------
SOURCES_PREFERRED_CODES = ["ALIAPUR", "COREPILE"]
ENVIRONMENTS = ["DEV", "PREPROD", "PROD"]
# URLs de la DB
DB_URLS = {
    "DEV": os.environ.get("DB_URL_DEV"),
    "PREPROD": os.environ.get("DB_URL_PREPROD"),
    "PROD": os.environ.get("DB_URL_PROD"),
}
# Chemin vers le fichier CSV
CURRENT_DIR = Path(__file__).resolve().parent
CLUSTERING_CSV_FILEPATH = CURRENT_DIR / "./20241121_dedup_dechetteries.csv"

# Colonnes pour le debug
COLS_DEBUG = ["cluster_id", "identifiant_unique", "children_count", "source_id"]


def environment_setup() -> Tuple[Engine, list, Path]:
    """Choix de l'environnement et retourne les paramètres nécessaires

    Returns:
        db_engine (Engine): connexion à la base de données
        clusters_done_list: liste des clusters traités
        clusters_done_path: chemin vers le fichier de suivi des clusters traités
    """

    banner("Setup de l'environnement")
    print("DB_URLS:")
    for env, url in DB_URLS.items():
        print(f"{env}={url}")
    assert any(
        DB_URLS.values()
    ), f"""URLs DB manquantes: besoin os.environ sur 1 de
        {["DB_URL_" + env for env in ENVIRONMENTS]}"""

    env_name = Prompt.ask("Environnement", choices=ENVIRONMENTS)
    db_url = DB_URLS[env_name]
    assert db_url, "db_url est vide"
    db_engine = create_engine(db_url)

    # Fichier de suivi des clusters traités construit à partir de l'environnement
    clusters_done_path = CURRENT_DIR / f"./clusters_done_{env_name.lower()}.json"
    clusters_done_list = []
    if not clusters_done_path.exists():
        clusters_done_path.write_text(json.dumps(clusters_done_list, indent=4))
    else:
        clusters_done_list = json.loads(clusters_done_path.read_text())

    print(f"{env_name=}")
    print(f"{db_url=}")
    print(f"{db_engine=}")
    print(f"{clusters_done_path=}")
    print(f"{len(clusters_done_list)=}")

    # Doesn't understand that db_engine is of proper type Engine
    return db_engine, clusters_done_list, clusters_done_path  # type: ignore


def main() -> None:
    """Fonction principale qui regroupe toute là logique de déduplication"""
    banner(__file__)

    DRY_RUN = Confirm.ask("DRY RUN (càd pas de modifications DB)?")

    print(f"{DRY_RUN=}")
    if not DRY_RUN:
        if not Confirm.ask("\n🔴 Modifications DB à venir: continuer? 🔴"):
            raise SystemExit("Interrompu par l'utilisateur")

    # ------------------------------------------
    # SETUP D'ENVIRONNEMENT
    # ------------------------------------------
    db_engine, clusters_done_list, clusters_done_path = environment_setup()

    # ------------------------------------------
    # DONNEES D'ENTREE
    # ------------------------------------------
    # Chaque ligne est un cluster_id <-> acteur identifiant_unique
    df_src = source_data_get(CLUSTERING_CSV_FILEPATH)

    # ------------------------------------------
    # CALCUL DU NOMBRE D'ENFANTS PAR PARENT
    # ------------------------------------------
    # Utiliser dans la logique de clustering
    # pour privilégier les parents avec le plus d'enfants
    banner("CALCUL DU NOMBRE D'ENFANTS SUR LES PARENTS")
    # TODO: remplacer par une requête Django utilisant modèle RevisionActeur
    df_revision_with_parents_db = pd.read_sql(
        """SELECT identifiant_unique, parent_id
        FROM qfdmo_revisionacteur WHERE parent_id IS NOT NULL;""",
        db_engine,
    )
    # MAPPING parent_id -> identifiant_unique
    parent_ids_to_identifiant_ids_db = df_mapping_one_to_many(
        "parent_ids_to_identifiant_ids_db",
        df_revision_with_parents_db,
        "parent_id",
        "identifiant_unique",
    )
    # MAPPING parent_id -> nombre d'enfants
    parent_ids_to_children_count_db = {
        k: len(v) for k, v in parent_ids_to_identifiant_ids_db.items()
    }

    # ------------------------------------------
    # RECUPERATION IDS DES SOURCES PREFEREES
    # ------------------------------------------
    # Pour privilégier certaines sources au moment de la création des parents
    banner("RECUPERATION IDS DES SOURCES PREFEREES")
    # TODO: remplacer par une requête Django utilisant modèle Source
    query_source = "SELECT id, code FROM qfdmo_source"
    sources = pd.read_sql_query(query_source, db_engine)
    sources_preferred_ids = sources[sources["code"].isin(SOURCES_PREFERRED_CODES)][
        "id"
    ].tolist()
    print(f"{SOURCES_PREFERRED_CODES=}", f"{sources_preferred_ids=}")

    # ------------------------------------------
    # GESTION DES CLUSTERS
    # ------------------------------------------
    banner("GESTION DES CLUSTERS")
    df_src = df_src.sort_values("cluster_id", ascending=True)
    for cluster in df_src.groupby("cluster_id"):

        # ------------------------------------------
        # Préparation et debug:
        # - split cluster_id et acteurs à partir du groupby
        # - récupération des identifiants uniques
        cluster_id, acteurs = cluster
        identifiants_uniques = acteurs["identifiant_unique"].tolist()
        # On vérifie si le cluster a déjà été traité
        cluster_is_done = cluster_id in clusters_done_list
        # On skip si est on en mode test et que le cluster n'est pas dans la liste
        if CLUSTER_IDS_TO_CHANGES and cluster_id not in CLUSTER_IDS_TO_CHANGES:
            continue
        banner(f"CLUSTER: {cluster_id=}")
        print(f"{cluster_id=}", f"{identifiants_uniques=}", f"{cluster_is_done=}")
        # On skip les clusters déjà traités
        if cluster_is_done:
            continue

        # ------------------------------------------
        # Gestion du cluster en DB
        changes: List[Change] = db_manage_cluster(
            db_engine,
            # Doesn't understand that from .groupby we get a string for cluster_id
            cluster_id,  # type: ignore
            identifiants_uniques,
            parent_ids_to_children_count_db,
            sources_preferred_ids,
            is_dry_run=DRY_RUN,
        )
        print(f"\tchangements:{changes=}")

        # ------------------------------------------
        # Vérifications des changements obtenurs
        # vs. les changements attendus
        if CLUSTER_IDS_TO_CHANGES and cluster_id in CLUSTER_IDS_TO_CHANGES:
            changes_exp: List[Change] = CLUSTER_IDS_TO_CHANGES[cluster_id]
            # Conversion en dataframes pour faciliter la comparaison
            debug_act = pd.DataFrame(changes).rename(columns={"operation": "op_actual"})
            debug_exp = pd.DataFrame(changes_exp).rename(
                columns={"operation": "op_expected"}
            )
            debug = pd.merge(debug_act, debug_exp, on="acteur_id", how="outer")
            debug["match"] = debug["op_actual"] == debug["op_expected"]
            print(debug[["acteur_id", "op_actual", "op_expected", "match"]])
            if not debug["match"].all():
                raise AssertionError(f"Incohérences de changements pour {cluster_id=}")
            print(f"✅ Changements cohérents pour {cluster_id=}")
            if not Confirm.ask("\nContinuer sur le prochain cluster?"):
                raise SystemExit("Interrompu par l'utilisateur")

        # Sauvegarde de l'avancement
        if not DRY_RUN:
            clusters_done_list.append(cluster_id)
            clusters_done_path.write_text(json.dumps(clusters_done_list, indent=4))


if __name__ == "__main__":
    main()
