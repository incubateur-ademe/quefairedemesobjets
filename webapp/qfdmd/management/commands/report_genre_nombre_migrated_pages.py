import decouple
from django.core.management.base import BaseCommand, CommandError

from qfdmd.genre_nombre_classification import (
    GENRE_NOMBRE_CSV,
    classify_with_ollama,
    load_csv_lookup,
    write_report,
)
from qfdmd.models import ProduitPage


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
        csv_lookup = load_csv_lookup(options["csv_path"])

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
                    genre_nombre = classify_with_ollama(
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

        write_report(options["output"], rows, extra_fieldnames=["page_id"])

        from_csv = sum(1 for r in rows if r["source"] == "csv")
        from_llm = sum(1 for r in rows if r["source"] == "llm")
        self.stdout.write(
            self.style.SUCCESS(
                f"{len(rows)} page(s) écrite(s) dans {options['output']} "
                f"({from_csv} depuis le CSV, {from_llm} classifiée(s) par le LLM)."
            )
        )
