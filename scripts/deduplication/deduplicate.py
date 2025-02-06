"""
Script pour dédupliquer les acteurs:

Voir README.md pour usage

Nommage des variables:
 - suffixe "_src" pour la donnée de source
 - suffixe "_db" pour la donnée en base de données
"""

import importlib
import json
from pathlib import Path

import pandas as pd
import utils.django_setup  # noqa: F401
from django.conf import settings
from django.db.models import Count
from models.change import Change
from rich import print
from rich.prompt import Confirm
from rich.traceback import install
from tasks.db_manage_cluster import db_manage_cluster
from tasks.source_data_get import source_data_get
from utils.cli import banner
from utils.db import db_source_ids_by_code_get

from qfdmo.models import RevisionActeur

install()  # you can install globally to your env, see docs

DIR_CURRENT = Path(__file__).resolve().parent

# ------------------------------------------
# PARAMETRES DU RUN
# ------------------------------------------
# A adapter
RUN_SOURCES_PREFERRED_CODES = ["ALIAPUR", "COREPILE"]
RUN_ID = "dechetteries_202412"
RUN_CLUSTER_IDS_TO_SKIP = [
    "85250_3_1",
    "93320_1_1",
]  # Si besoin pour passer des erreurs

# Automatique par le script
RUN_CLUSTER_IDS_TO_CHANGES = getattr(
    importlib.import_module(f"runs.{RUN_ID}.verifications"),
    "RUN_CLUSTER_IDS_TO_CHANGES",
)
RUN_FILEPATH_CLUSTER_DATA = DIR_CURRENT / f"./runs/{RUN_ID}/clusters.csv"
RUN_FILEPATH_CLUSTERS_DONE = None  # laisser None, définit par le script

# sur certains clusters


# ------------------------------------------
# AUTRES PARAMETRES
# ------------------------------------------
# Colonnes pour le debug
COLS_DEBUG = ["cluster_id", "identifiant_unique", "children_count", "source_id"]

# Différent modes d'execution du script
MODE_DRY_RUN = None  # laisser None, définit par le script
MODE_INTERACTIVE = None  # laisser None, définit par le script


def environment_setup() -> tuple[list, Path]:
    """Choix de l'environnement et retourne les paramètres nécessaires

    Returns:
        clusters_done_list: liste des clusters traités
        clusters_done_path: chemin vers le fichier de suivi des clusters traités
    """
    db = settings.DATABASES["default"]
    print(f"DB utilisée par django: {db["HOST"]}:{db["PORT"]}/{db["NAME"]}")
    if not Confirm.ask("\nUtiliser? (sinon, changer l'env Django en fonction)"):
        raise SystemExit("Interrompu par l'utilisateur")

    # Fichier de suivi des clusters traités par environnement
    db_env = f"{db["HOST"]}_{db["PORT"]}_{db["NAME"]}"
    clusters_done_path = (
        DIR_CURRENT / f"./runs/{RUN_ID}/clusters_done_{db_env.lower()}.json"
    )
    clusters_done_list = []
    if not clusters_done_path.exists():
        clusters_done_path.write_text(json.dumps(clusters_done_list, indent=4))
    else:
        clusters_done_list = json.loads(clusters_done_path.read_text())

    print(f"{db_env=}")
    print(f"{clusters_done_path=}")
    print(f"{clusters_done_list=}")

    return clusters_done_list, clusters_done_path


def main() -> None:
    """Fonction principale qui regroupe toute là logique de déduplication"""
    banner(__file__)

    banner("Mode dry run")
    print("DRY RUN = pas de modif DB, seuls clusters de vérifications traités")
    MODE_DRY_RUN = Confirm.ask("\nMode dry run ?")
    print(f"{MODE_DRY_RUN=}")
    if not MODE_DRY_RUN:
        if not Confirm.ask("\n🔴 Modifications DB à venir: continuer? 🔴"):
            raise SystemExit("Interrompu par l'utilisateur")

    # ------------------------------------------
    # SETUP D'ENVIRONNEMENT
    # ------------------------------------------
    banner("SETUP ENVIRONNEMENT")
    clusters_done_list, clusters_done_path = environment_setup()

    # ------------------------------------------
    # MODE INTERACTIF
    # ------------------------------------------
    banner("Mode interactif")
    print(
        """\n🔴 Dernière chance de controle du script: si pas interactif,
          tous les clusters seront traités sans possibilité de pause 🔴"""
    )
    MODE_INTERACTIVE = Confirm.ask("\nMode interactif?")
    print(f"{MODE_INTERACTIVE=}")

    # ------------------------------------------
    # DONNEES D'ENTREE
    # ------------------------------------------
    # Chaque ligne est un cluster_id <-> acteur identifiant_unique
    df_src = source_data_get(RUN_FILEPATH_CLUSTER_DATA)

    # ------------------------------------------
    # CALCUL DU NOMBRE D'ENFANTS PAR PARENT
    # ------------------------------------------
    # Utiliser dans la logique de clustering
    # pour privilégier les parents avec le plus d'enfants
    # Créer un mapping parent_id -> nombre d'enfants
    banner("CALCUL DU NOMBRE D'ENFANTS SUR LES PARENTS")
    parent_ids_to_children_count_db = (
        RevisionActeur.objects.filter(parent_id__isnull=False)
        .values("parent_id")
        .annotate(count=Count("identifiant_unique"))
    )
    parent_ids_to_children_count_db = {
        x["parent_id"]: x["count"] for x in parent_ids_to_children_count_db
    }

    # ------------------------------------------
    # RECUPERATION IDS DES SOURCES PREFEREES
    # ------------------------------------------
    # Pour privilégier certaines sources au moment de la création des parents
    banner("RECUPERATION IDS DES SOURCES PREFEREES")
    source_ids_by_codes = db_source_ids_by_code_get()
    sources_preferred_ids = [
        source_ids_by_codes[x] for x in RUN_SOURCES_PREFERRED_CODES
    ]
    print(f"{RUN_SOURCES_PREFERRED_CODES=}", f"{sources_preferred_ids=}")

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

        # On passe si le cluster est dans la liste à skip
        if cluster_id in RUN_CLUSTER_IDS_TO_SKIP:
            print(f"⚠️ Cluster à passer: {cluster_id=}")
            continue

        # On passe si dry run et le cluster n'est pas dans la liste
        # des vérifications
        if (
            MODE_DRY_RUN
            and RUN_CLUSTER_IDS_TO_CHANGES
            and cluster_id not in RUN_CLUSTER_IDS_TO_CHANGES
        ):
            continue

        # On vérifie si le cluster a déjà été traité
        cluster_is_done = cluster_id in clusters_done_list

        banner(f"CLUSTER: {cluster_id=}")
        print(f"{cluster_id=}", f"{identifiants_uniques=}", f"{cluster_is_done=}")
        # On skip les clusters déjà traités
        if cluster_is_done:
            continue

        # ------------------------------------------
        # Gestion du cluster en DB
        changes: list[Change] = db_manage_cluster(
            # Pylance doesn't get that from .groupby we get a string for cluster_id
            cluster_id,  # type: ignore
            identifiants_uniques,
            parent_ids_to_children_count_db,
            sources_preferred_ids,
            is_dry_run=MODE_DRY_RUN,
        )
        print(f"\tchangements:{changes=}")
        print(f"\n{cluster_id=} traité ✅")

        # ------------------------------------------
        # Vérifications des changements obtenus
        # vs. changements attendus
        if RUN_CLUSTER_IDS_TO_CHANGES and cluster_id in RUN_CLUSTER_IDS_TO_CHANGES:
            changes_exp: list[Change] = RUN_CLUSTER_IDS_TO_CHANGES[cluster_id]  # type: ignore
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

        # Sauvegarde de l'avancement
        if not MODE_DRY_RUN:
            clusters_done_list.append(cluster_id)
            clusters_done_path.write_text(json.dumps(clusters_done_list, indent=4))

        if MODE_INTERACTIVE:
            if not Confirm.ask("\nContinuer sur le prochain cluster?"):
                raise SystemExit("Interrompu par l'utilisateur")


if __name__ == "__main__":
    main()
