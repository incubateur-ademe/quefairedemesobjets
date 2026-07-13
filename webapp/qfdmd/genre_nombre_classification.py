"""Shared helpers for the genre/nombre report management commands.

Both report_genre_nombre_migrated_pages and report_genre_nombre_synonymes
look up (produit_id, nom) pairs in genre-nombre.csv, falling back to a
local Ollama instance when a pair is missing, and write the same report
CSV shape.
"""

import csv
import json

import requests

GENRE_NOMBRE_CSV = "genre-nombre.csv"
REPORT_FIELDNAMES = ["produit_id", "synonyme_nom", "genre", "nombre", "source"]

OLLAMA_MODEL = "mistral:7b-instruct"
OLLAMA_SYSTEM_PROMPT = (
    "Tu es un expert en grammaire française. Pour un nom commun donné, "
    "détermine son genre (masculin ou féminin) et son nombre (singulier ou "
    "pluriel) tels qu'ils apparaissent dans le texte. Réponds uniquement en "
    "JSON."
)
OLLAMA_FORMAT = {
    "type": "object",
    "properties": {
        "genre": {"type": "string", "enum": ["masculin", "feminin"]},
        "nombre": {"type": "string", "enum": ["singulier", "pluriel"]},
    },
    "required": ["genre", "nombre"],
}


def load_csv_lookup(path: str) -> dict[tuple[int, str], tuple[str, str]]:
    """Return {(produit_id, nom): (genre, nombre)} from the genre-nombre CSV."""
    lookup = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lookup[(int(row["produit"]), row["nom"])] = (row["genre"], row["nombre"])
    return lookup


def classify_with_ollama(base_url: str, nom: str) -> tuple[str, str]:
    """Ask the local Ollama instance for (genre, nombre) of ``nom``."""
    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": OLLAMA_SYSTEM_PROMPT},
                {"role": "user", "content": f"Nom: {nom}"},
            ],
            "stream": False,
            "format": OLLAMA_FORMAT,
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["message"]["content"]
    parsed = json.loads(content)
    return parsed["genre"], parsed["nombre"]


def write_report(output_path: str, rows: list[dict], extra_fieldnames: list[str] = ()):
    fieldnames = [*extra_fieldnames, *REPORT_FIELDNAMES]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
