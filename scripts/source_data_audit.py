"""
Script pour auditer la donnée d'une source, détecter
des problèmes potentiels, et accélérer le développement
des DAGs (en identifiant les problèmes en amont).
"""

import os
import re
import webbrowser
from pathlib import Path

import numpy as np
import pandas as pd
from rich import print
from rich.prompt import Confirm, Prompt
from rich.traceback import install
from ydata_profiling import ProfileReport

from dags.sources.tasks.business_logic.source_data_download import source_data_download
from dags.sources.tasks.transform.transform_column import clean_siret

install()

DIR_CURRENT = Path(os.path.dirname(os.path.realpath(__file__)))
COLUMNS_RENAMES = {
    "id_point_apport_ou_reparation": "identifiant_externe",
}


def banner(text: str) -> None:
    """
    Affiche une banière pour aider à relire les logs CLI
    Args:
        text: texte à afficher
    """
    print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    print(f"[bold cyan]{text}[/bold cyan]")
    print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")


def main():

    # ----------------------------------------------
    # 0. Config
    # ----------------------------------------------
    banner("0. Config")
    url = Prompt.ask("URL du fichier source")
    print(f"{url=}")
    print(f"{COLUMNS_RENAMES=}")

    if not Confirm.ask("\nContinuer?"):
        raise SystemExit("Interrompu par l'utilisateur")

    # ----------------------------------------------
    # 1. Téléchargement des données
    # ----------------------------------------------
    banner("1. Téléchargement des données")
    filename = re.sub(r"https?://[^/]+/(.*)", r"\1", url)
    filename = re.sub(r"[^a-zA-Z0-9]", "_", filename)
    path_data_csv = DIR_CURRENT / f"{filename}.csv"
    path_report_html = DIR_CURRENT / f"{filename}.html"
    print("🔽 Téléchargement des données:")
    print(f"\t - {url=}")
    print(f"\t - {path_data_csv=}")
    print(f"\t - {path_data_csv.exists()=}")
    if path_data_csv.exists():
        print("\t - Utilisation du fichier local")
        df = pd.read_csv(path_data_csv).replace({np.nan: None})
    else:
        print("\t - Téléchargement de la donnée")
        if not Confirm.ask("\nContinuer?"):
            raise SystemExit("Interrompu par l'utilisateur")
        df = source_data_download(url)
        df.to_csv(path_data_csv, index=False)

    # ----------------------------------------------
    # 2. Structure de la dataframe
    # ----------------------------------------------
    banner("2. Structure de la dataframe")
    print("Taille:")
    print(f"{df.shape}")

    print("\nColonnes:")
    print("\n".join(sorted(df.columns.tolist())))

    # ----------------------------------------------
    # 3. Description succincte
    # ----------------------------------------------
    banner("3. Description succincte")
    print(f"{df.describe()=}")

    # ----------------------------------------------
    # 4. Création du rapport HTML ydata-profiling
    # ----------------------------------------------
    banner("4. Création du rapport HTML ydata-profiling")
    if not Confirm.ask("\nPasser?"):
        print(f"{path_report_html=}")
        profile = ProfileReport(df, title="Profiling")
        path_report_html.write_text(profile.to_html())
        print("Rapport HTML généré")
        webbrowser.open(f"file://{path_report_html}")

    # ----------------------------------------------
    # 5. Vérifications métiers spécifiques à LVAO
    # ----------------------------------------------
    banner("5. Vérifications métiers spécifiques à LVAO")
    df = df.rename(columns=COLUMNS_RENAMES)

    # identifiant_externe
    print(" - colonne: identifiant_externe = ", end="\r")
    if "identifiant_externe" not in df.columns:
        raise ValueError("Besoin d'un identifiant externe")
    else:
        dups = df[df["identifiant_externe"].duplicated(keep=False)]
        if not dups.empty:
            print("Doublons:")
            print(dups)
            raise ValueError("Doublons sur identifiant_externe")
        print("\t - colonne: identifiant_externe = ✅ (pas de doublons)")

    # siret
    if "siret" in df.columns:
        print(" - colonne: siret = ", end="\r")
        sirets = df["siret"].dropna().unique().tolist()
        sirets_invalid = [x for x in sirets if clean_siret(x) is None]
        if sirets_invalid:
            print(f"{len(sirets_invalid)=}")
            for siret in sirets_invalid[:10]:
                print(f"\t{siret=}", f"{len(siret)=}")
            print("[bold red]SIRET invalides, voir échantillon ci-dessus[/bold red]")
        print("\t - colonne: siret = ✅ (format valide)")


if __name__ == "__main__":
    main()
