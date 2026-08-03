import csv
from unittest.mock import patch

import pytest
from django.core.management import call_command

from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory

pytestmark = pytest.mark.django_db


def _write_csv(tmp_path, rows):
    path = tmp_path / "genre-nombre.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "produit", "nom", "premier_mot", "genre", "nombre"]
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


class TestReportGenreNombreSynonymes:
    def test_covers_every_synonyme_not_just_main_ones(self, tmp_path):
        produit = ProduitFactory(nom="Rideau")
        SynonymeFactory(produit=produit, nom="Rideau")
        SynonymeFactory(produit=produit, nom="Voilage")

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
                },
                {
                    "id": 2,
                    "produit": produit.pk,
                    "nom": "Voilage",
                    "premier_mot": "Voilage",
                    "genre": "masculin",
                    "nombre": "singulier",
                },
            ],
        )
        output_path = tmp_path / "genre-nombre-synonyme.csv"

        call_command(
            "report_genre_nombre_synonymes",
            csv_path=str(csv_path),
            output=str(output_path),
            no_llm=True,
        )

        with open(output_path, newline="", encoding="utf-8") as f:
            rows = {r["synonyme_nom"] for r in csv.DictReader(f)}

        assert rows == {"Rideau", "Voilage"}

    def test_falls_back_to_llm_when_pair_missing_from_csv(self, tmp_path):
        produit = ProduitFactory(nom="Rideau")
        SynonymeFactory(produit=produit, nom="Tabouret")

        csv_path = _write_csv(tmp_path, [])
        output_path = tmp_path / "genre-nombre-synonyme.csv"

        with patch(
            "qfdmd.management.commands.report_genre_nombre_synonymes"
            ".classify_with_ollama",
            return_value=("masculin", "singulier"),
        ) as mocked_classify:
            call_command(
                "report_genre_nombre_synonymes",
                csv_path=str(csv_path),
                output=str(output_path),
            )

        mocked_classify.assert_called_once()
        assert mocked_classify.call_args.args[1] == "Tabouret"

        with open(output_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 1
        assert rows[0]["source"] == "llm"

    def test_no_llm_skips_synonymes_missing_from_csv(self, tmp_path):
        produit = ProduitFactory(nom="Rideau")
        SynonymeFactory(produit=produit, nom="Tabouret")

        csv_path = _write_csv(tmp_path, [])
        output_path = tmp_path / "genre-nombre-synonyme.csv"

        call_command(
            "report_genre_nombre_synonymes",
            csv_path=str(csv_path),
            output=str(output_path),
            no_llm=True,
        )

        with open(output_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert rows == []

    def test_does_not_write_to_database(self, tmp_path):
        produit = ProduitFactory(nom="Rideau")
        synonyme = SynonymeFactory(produit=produit, nom="Rideau")

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
            "report_genre_nombre_synonymes",
            csv_path=str(csv_path),
            output=str(tmp_path / "genre-nombre-synonyme.csv"),
            no_llm=True,
        )

        # Synonyme has no genre/nombre fields at all; just confirm the
        # command didn't error trying to write to the model.
        synonyme.refresh_from_db()
