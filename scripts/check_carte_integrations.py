#!/usr/bin/env python3
"""
Script pour détecter les intégrations de la carte via script ou iframe sur les sites
listés dans un CSV.
"""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup
from tqdm import tqdm

# Désactiver les avertissements SSL pour les certificats auto-signés
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Essayer d'importer playwright, sinon utiliser requests uniquement
try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning(
        "Playwright non disponible. Les pages JavaScript ne seront pas exécutées. "
        "Installez avec: pip install playwright && playwright install chromium"
    )

# User-Agent pour éviter les blocages
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

# Domaines valides pour les intégrations de la carte
VALID_DOMAINS = [
    "lvao.ademe.fr",
    "quefairedemesdechets.ademe.fr",
    "quefairedemesdechets.fr",
    "quefairedemesobjets.ademe.fr",
    "quefairedemesobjets.fr",
]


def read_csv_file(csv_path: Path) -> list[str]:
    """
    Lit le CSV et extrait les URLs de la colonne "Lien carte ou données".

    Args:
        csv_path: Chemin vers le fichier CSV

    Returns:
        Liste des URLs valides (non vides)
    """
    urls = []
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # Lire l'en-tête

            # Trouver l'index de la colonne "Lien carte ou données"
            try:
                url_column_index = headers.index("Lien carte ou données")
            except ValueError:
                logger.error('Colonne "Lien carte ou données" introuvable dans le CSV')
                return []

            # Extraire les URLs
            for row_num, row in enumerate(reader, start=2):
                if len(row) > url_column_index:
                    url = row[url_column_index].strip()
                    if url and url not in ("", "?"):
                        urls.append(url)
                else:
                    logger.warning(f"Ligne {row_num}: pas assez de colonnes, ignorée")

        logger.info(f"{len(urls)} URLs trouvées dans le CSV")
        return urls

    except Exception as e:
        logger.error(f"Erreur lors de la lecture du CSV: {e}")
        return []


def fetch_page_content(
    url: str, timeout: int = 10, use_playwright: bool = True
) -> tuple[str | None, str | None]:
    """
    Fait une requête HTTP GET et retourne le contenu HTML.
    Utilise Playwright si disponible pour exécuter JavaScript.

    Args:
        url: URL à récupérer
        timeout: Timeout en secondes
        use_playwright: Si True, utilise Playwright pour exécuter JavaScript

    Returns:
        Tuple (html_content, error_message) où error_message est None si succès
    """
    # Essayer Playwright si disponible et demandé
    if use_playwright and PLAYWRIGHT_AVAILABLE:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1920, "height": 1080},
                    ignore_https_errors=True,  # Ignorer les erreurs SSL
                )
                page = context.new_page()

                # Naviguer vers la page (timeout en millisecondes pour Playwright)
                # On utilise "domcontentloaded" pour être plus rapide, puis on attend
                # networkidle
                page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)

                # Attendre que le réseau soit stable pour que le JavaScript s'exécute
                # On utilise un timeout plus court pour éviter d'attendre trop longtemps
                try:
                    page.wait_for_load_state(
                        "networkidle", timeout=min(timeout * 1000, 15000)
                    )
                except PlaywrightTimeoutError:
                    # Si networkidle prend trop de temps, on attend juste un peu
                    # pour que le JavaScript basique s'exécute
                    page.wait_for_timeout(2000)  # Attendre 2 secondes

                # Récupérer le HTML après exécution du JavaScript
                html_content = page.content()

                browser.close()
                return (html_content, None)

        except PlaywrightTimeoutError:
            error_msg = f"Timeout Playwright après {timeout}s"
            logger.warning(f"{url}: {error_msg}")
            return (None, error_msg)

        except Exception as e:
            error_msg = f"Erreur Playwright: {str(e)}"
            logger.warning(f"{url}: {error_msg}")
            # Fallback sur requests en cas d'erreur Playwright
            return fetch_page_content(url, timeout, use_playwright=False)

    # Fallback sur requests si Playwright n'est pas disponible ou en cas d'erreur
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
            verify=False,  # Ignorer les erreurs SSL (certificats auto-signés)
        )
        response.raise_for_status()
        return (response.text, None)

    except requests.exceptions.Timeout:
        error_msg = f"Timeout après {timeout}s"
        logger.warning(f"{url}: {error_msg}")
        return (None, error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Erreur HTTP: {str(e)}"
        logger.warning(f"{url}: {error_msg}")
        return (None, error_msg)

    except Exception as e:
        error_msg = f"Erreur inattendue: {str(e)}"
        logger.warning(f"{url}: {error_msg}")
        return (None, error_msg)


def parse_html(html: str) -> BeautifulSoup:
    """
    Parse le HTML avec BeautifulSoup.

    Args:
        html: Contenu HTML à parser

    Returns:
        Objet BeautifulSoup
    """
    return BeautifulSoup(html, "html.parser")


def find_script_integration(soup: BeautifulSoup) -> dict[str, Any] | None:
    """
    Cherche un tag <script> avec src contenant l'un des domaines valides.

    Args:
        soup: Objet BeautifulSoup

    Returns:
        Dict avec path, url_params et data_attributes, ou None si non trouvé
    """
    scripts = soup.find_all("script", src=True)

    for script in scripts:
        src = script.get("src", "")
        if not src or not isinstance(src, str):
            continue
        if any(domain in src for domain in VALID_DOMAINS):
            # Extraire le path et les paramètres URL
            parsed_url = urlparse(src)
            path = parsed_url.path
            url_params = parse_qs(parsed_url.query)

            # Extraire tous les attributs data-*
            data_attributes = {}
            for attr_name, attr_value in script.attrs.items():
                if attr_name.startswith("data-"):
                    # Enlever le préfixe "data-" et garder le reste
                    key = attr_name[5:]  # Enlever "data-"
                    data_attributes[key] = attr_value

            return {
                "path": path,
                "url_params": url_params,
                "data_attributes": data_attributes,
            }

    return None


def find_iframe_integration(soup: BeautifulSoup) -> dict[str, Any] | None:
    """
    Cherche un tag <iframe> avec src contenant l'un des domaines valides.

    Args:
        soup: Objet BeautifulSoup

    Returns:
        Dict avec path et url_params, ou None si non trouvé
    """
    iframes = soup.find_all("iframe", src=True)

    for iframe in iframes:
        src = iframe.get("src", "")
        if not src or not isinstance(src, str):
            continue
        if any(domain in src for domain in VALID_DOMAINS):
            # Extraire le path et les paramètres URL
            parsed_url = urlparse(src)
            path = parsed_url.path
            url_params = parse_qs(parsed_url.query)

            return {
                "path": path,
                "url_params": url_params,
            }

    return None


def check_integration(url: str) -> dict[str, Any]:
    """
    Fonction principale qui orchestre le scraping d'une URL.

    Args:
        url: URL à analyser

    Returns:
        Dict avec les résultats de l'analyse
    """
    result: dict[str, Any] = {
        "url": url,
        "integration_type": None,
        "found": False,
        "path": None,
        "url_params": None,
        "data_attributes": None,
        "error": None,
    }

    # Récupérer le contenu de la page
    html_content, error = fetch_page_content(url)
    if error:
        result["error"] = error
        return result

    if not html_content:
        result["error"] = "Contenu HTML vide"
        return result

    # Parser le HTML
    try:
        soup = parse_html(html_content)
    except Exception as e:
        result["error"] = f"Erreur lors du parsing HTML: {str(e)}"
        return result

    # Chercher d'abord un script
    script_result = find_script_integration(soup)
    if script_result:
        result["integration_type"] = "script"
        result["found"] = True
        result["path"] = script_result["path"]
        result["url_params"] = script_result["url_params"]
        result["data_attributes"] = script_result["data_attributes"]
        return result

    # Si aucun script trouvé, chercher une iframe
    iframe_result = find_iframe_integration(soup)
    if iframe_result:
        result["integration_type"] = "iframe"
        result["found"] = True
        result["path"] = iframe_result["path"]
        result["url_params"] = iframe_result["url_params"]
        return result

    # Aucune intégration trouvée
    return result


def process_csv(input_csv: Path, output_csv: Path) -> None:
    """
    Traite le CSV d'entrée et écrit les résultats dans le CSV de sortie.

    Args:
        input_csv: Chemin vers le CSV d'entrée
        output_csv: Chemin vers le CSV de sortie
    """
    # Récupérer la liste des URLs
    urls = read_csv_file(input_csv)
    if not urls:
        logger.error("Aucune URL trouvée dans le CSV")
        return

    # Traiter chaque URL
    results = []
    for url in tqdm(urls, desc="Analyse des URLs"):
        result = check_integration(url)
        results.append(result)

    # Écrire les résultats dans le CSV de sortie
    fieldnames = [
        "url",
        "integration_type",
        "integration_path",
        "integration_url_params",
        "integration_data_attributes",
        "integration_error",
    ]

    try:
        with output_csv.open("w", encoding="utf-8", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                row = {
                    "url": result["url"],
                    "integration_type": result["integration_type"] or "",
                    "integration_path": result["path"] or "",
                    "integration_url_params": (
                        json.dumps(result["url_params"]) if result["url_params"] else ""
                    ),
                    "integration_data_attributes": (
                        json.dumps(result["data_attributes"])
                        if result["data_attributes"]
                        else ""
                    ),
                    "integration_error": result["error"] or "",
                }
                writer.writerow(row)

        logger.info(f"Résultats écrits dans {output_csv}")
        logger.info(
            f"Intégrations trouvées: {sum(1 for r in results if r['found'])}/"
            f"{len(results)}"
        )

    except Exception as e:
        logger.error(f"Erreur lors de l'écriture du CSV: {e}")
        sys.exit(1)


def main() -> None:
    """Point d'entrée du script."""
    parser = argparse.ArgumentParser(
        description="Détecte les intégrations de la carte via script ou iframe"
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Chemin vers le fichier CSV d'entrée",
    )
    parser.add_argument(
        "output_csv",
        type=Path,
        help="Chemin vers le fichier CSV de sortie",
    )

    args = parser.parse_args()

    # Vérifier que le fichier d'entrée existe
    if not args.input_csv.exists():
        logger.error(f"Fichier d'entrée introuvable: {args.input_csv}")
        sys.exit(1)

    # Créer le répertoire de sortie si nécessaire
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)

    # Traiter le CSV
    process_csv(args.input_csv, args.output_csv)


if __name__ == "__main__":
    main()
