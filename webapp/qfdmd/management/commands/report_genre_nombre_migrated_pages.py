import csv
import json

import decouple
import requests
from django.core.management.base import BaseCommand, CommandError

from qfdmd.models import ProduitPage

GENRE_NOMBRE_CSV = "genre-nombre.csv"

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


def _load_csv_lookup(path: str) -> dict[tuple[int, str], tuple[str, str]]:
    """Return {(produit_id, nom): (genre, nombre)} from the genre-nombre CSV."""
    lookup = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lookup[(int(row["produit"]), row["nom"])] = (row["genre"], row["nombre"])
    return lookup


def _classify_with_ollama(base_url: str, nom: str) -> tuple[str, str]:
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


class Command(BaseCommand):
    help = (
        "Reports genre/nombre for the main synonyme of every migrated "
        "ProduitPage: looked up from genre-nombre.csv, falling back to a "
        "local Ollama instance (OLLAMA_BASE_URL) when the pair "
        "(produit_id, nom) isn't in the CSV. Writes a report CSV, no "
        "database writes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv-path",
            default=GENRE_NOMBRE_CSV,
            help=f"Path to the genre-nombre CSV (default: {GENRE_NOMBRE_CSV}).",
        )
        parser.add_argument(
            "--output",
            default="genre_nombre_report.csv",
            help="Path to write the report CSV to.",
        )
        parser.add_argument(
            "--no-llm",
            action="store_true",
            help="Skip the Ollama fallback; leave genre/nombre blank when "
            "missing from the CSV.",
        )

    def handle(self, *args, **options):
        csv_lookup = _load_csv_lookup(options["csv_path"])

        ollama_base_url = decouple.config("OLLAMA_BASE_URL", default="")
        if not options["no_llm"] and not ollama_base_url:
            raise CommandError(
                "OLLAMA_BASE_URL is not set. Set it to your local Ollama "
                "instance URL, or pass --no-llm to skip the LLM fallback."
            )

        rows = []
        pages = ProduitPage.objects.filter(
            automatically_migrated_from_legacy_produit=True
        ).select_related()

        for page in pages:
            produit = page.linked_legacy_produit
            if produit is None:
                continue
            main_synonyme = produit.synonymes.filter(nom=produit.nom).first()
            if main_synonyme is None:
                continue

            key = (produit.pk, main_synonyme.nom)
            source = "csv"
            genre_nombre = csv_lookup.get(key)

            if genre_nombre is None and not options["no_llm"]:
                try:
                    genre_nombre = _classify_with_ollama(
                        ollama_base_url, main_synonyme.nom
                    )
                    source = "llm"
                except Exception as exc:  # noqa: BLE001
                    self.stdout.write(
                        self.style.ERROR(
                            f"Échec de classification pour "
                            f"« {main_synonyme.nom} » : {exc}"
                        )
                    )
                    continue

            if genre_nombre is None:
                continue

            genre, nombre = genre_nombre
            rows.append(
                {
                    "page_id": page.pk,
                    "produit_id": produit.pk,
                    "synonyme_nom": main_synonyme.nom,
                    "genre": genre,
                    "nombre": nombre,
                    "source": source,
                }
            )

        with open(options["output"], "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "page_id",
                    "produit_id",
                    "synonyme_nom",
                    "genre",
                    "nombre",
                    "source",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

        from_csv = sum(1 for r in rows if r["source"] == "csv")
        from_llm = sum(1 for r in rows if r["source"] == "llm")
        self.stdout.write(
            self.style.SUCCESS(
                f"{len(rows)} page(s) écrite(s) dans {options['output']} "
                f"({from_csv} depuis le CSV, {from_llm} classifiée(s) par le LLM)."
            )
        )
