import csv
from unittest.mock import patch

import pytest
from django.core.management import call_command
from wagtail.models import Page

from qfdmd.legacy_migration import migrate_produit
from qfdmd.models import LEGACY_PRODUIT_INDEX_SLUG, ProduitIndexPage
from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def index_dechet():
    root_page = Page.objects.get(depth=1)
    page = ProduitIndexPage(title="Déchets", slug=LEGACY_PRODUIT_INDEX_SLUG)
    root_page.add_child(instance=page)
    page.save()
    return page


def _write_csv(tmp_path, rows):
    path = tmp_path / "genre-nombre.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "produit", "nom", "premier_mot", "genre", "nombre"]
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


class TestReportGenreNombreMigratedPages:
    def test_uses_csv_when_pair_matches(self, index_dechet, tmp_path):
        produit = ProduitFactory(nom="Rideau")
        SynonymeFactory(produit=produit, nom="Rideau")
        migrate_produit(produit, index_page=index_dechet)
        produit.refresh_from_db()
        page = produit.legacy_imported_as_produit_page

        csv_path = _write_csv(
            tmp_path,
            [
                {
                    "id": 1,
                    "produit": produit.pk,
                    "nom": "Rideau",
                    "premier_mot": "Rideau",
                    "genre": "masculin",
                    "nombre": "singulier",
                }
            ],
        )
        output_path = tmp_path / "report.csv"

        call_command(
            "report_genre_nombre_migrated_pages",
            csv_path=str(csv_path),
            output=str(output_path),
            no_llm=True,
        )

        with open(output_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 1
        assert rows[0]["page_id"] == str(page.pk)
        assert rows[0]["genre"] == "masculin"
        assert rows[0]["nombre"] == "singulier"
        assert rows[0]["source"] == "csv"

    def test_falls_back_to_llm_when_pair_missing_from_csv(self, index_dechet, tmp_path):
        produit = ProduitFactory(nom="Tabouret")
        SynonymeFactory(produit=produit, nom="Tabouret")
        migrate_produit(produit, index_page=index_dechet)
        produit.refresh_from_db()

        csv_path = _write_csv(tmp_path, [])
        output_path = tmp_path / "report.csv"

        with patch(
            "qfdmd.management.commands.report_genre_nombre_migrated_pages"
            ".classify_with_ollama",
            return_value=("masculin", "singulier"),
        ) as mocked_classify:
            call_command(
                "report_genre_nombre_migrated_pages",
                csv_path=str(csv_path),
                output=str(output_path),
            )

        mocked_classify.assert_called_once()
        assert mocked_classify.call_args.args[1] == "Tabouret"

        with open(output_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 1
        assert rows[0]["source"] == "llm"
        assert rows[0]["genre"] == "masculin"
        assert rows[0]["nombre"] == "singulier"

    def test_no_llm_skips_pages_missing_from_csv(self, index_dechet, tmp_path):
        produit = ProduitFactory(nom="Tabouret")
        SynonymeFactory(produit=produit, nom="Tabouret")
        migrate_produit(produit, index_page=index_dechet)
        produit.refresh_from_db()

        csv_path = _write_csv(tmp_path, [])
        output_path = tmp_path / "report.csv"

        call_command(
            "report_genre_nombre_migrated_pages",
            csv_path=str(csv_path),
            output=str(output_path),
            no_llm=True,
        )

        with open(output_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert rows == []

    def test_does_not_write_to_database(self, index_dechet, tmp_path):
        """The report is read-only: it must not mutate ProduitPage."""
        produit = ProduitFactory(nom="Rideau")
        SynonymeFactory(produit=produit, nom="Rideau")
        migrate_produit(produit, index_page=index_dechet)
        produit.refresh_from_db()
        page = produit.legacy_imported_as_produit_page
        assert page.genre == ""

        csv_path = _write_csv(
            tmp_path,
            [
                {
                    "id": 1,
                    "produit": produit.pk,
                    "nom": "Rideau",
                    "premier_mot": "Rideau",
                    "genre": "masculin",
                    "nombre": "singulier",
                }
            ],
        )
        call_command(
            "report_genre_nombre_migrated_pages",
            csv_path=str(csv_path),
            output=str(tmp_path / "report.csv"),
            no_llm=True,
        )

        page.refresh_from_db()
        assert page.genre == ""
