"""
Fichier de test pour la fonction cluster_acteurs_read_parents
"""

import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_read.parents import (
    cluster_acteurs_read_parents,
)

from qfdmo.models import VueActeur
from unit_tests.qfdmo.acteur_factory import ActeurTypeFactory, SourceFactory


@pytest.mark.django_db()
class TestClusterActeursSelectionActeurTypeParents:

    @pytest.fixture
    def db_testdata_write(self) -> dict:
        data = {}
        data["at1"] = ActeurTypeFactory(code="at1")
        data["at2"] = ActeurTypeFactory(code="at2")
        data["at3"] = ActeurTypeFactory(code="at3")
        data["at4"] = ActeurTypeFactory(code="at4")
        data["s1"] = SourceFactory(code="s1")
        data["id_at1_parent"] = "10000000-0000-0000-0000-000000000000"
        data["id_at2_pas_parent"] = "20000000-0000-0000-0000-000000000000"
        data["id_at2_parent_a"] = "20000000-0000-0000-0000-00000000000a"
        data["id_at2_parent_b"] = "20000000-0000-0000-0000-00000000000b"
        data["id_at3_pas_parent"] = "30000000-0000-0000-0000-000000000000"
        data["id_at4_parent"] = "40000000-0000-0000-0000-000000000000"
        data["id_at4_parent_inactif"] = "40000000-0000-0000-0000-00000inactif"

        # at1
        # Parent MAIS d'un acteur type non sélectionné (at1)
        VueActeur.objects.create(
            acteur_type=data["at1"],
            identifiant_unique=data["id_at1_parent"],
        )
        # at2
        # On test le cas où il y a plusieurs parents
        # Pas parent car avec une source
        VueActeur.objects.create(
            acteur_type=data["at2"],
            identifiant_unique=data["id_at2_pas_parent"],
            source=data["s1"],
        )
        # Parents car sans source
        VueActeur.objects.create(
            nom="Mon parent at2 a",
            acteur_type=data["at2"],
            identifiant_unique=data["id_at2_parent_a"],
        )
        VueActeur.objects.create(
            nom="Mon PÂRËNT at2 b",
            acteur_type=data["at2"],
            identifiant_unique=data["id_at2_parent_b"],
        )
        # at3
        # Pour at3 on test le cas où il n'y a pas de parent
        VueActeur.objects.create(
            acteur_type=data["at3"],
            identifiant_unique=data["id_at3_pas_parent"],
            source=data["s1"],
        )
        # at4
        # On test le cas où il y a 1 parent
        VueActeur.objects.create(
            nom="Mon parent at4",
            acteur_type=data["at4"],
            identifiant_unique=data["id_at4_parent"],
        )
        # On test le cas où il y a 1 parent mais inactif
        VueActeur.objects.create(
            acteur_type=data["at4"],
            identifiant_unique=data["id_at4_parent_inactif"],
            statut="INACTIF",
        )

        return data

    @pytest.fixture
    def df_working(self, db_testdata_write) -> pd.DataFrame:
        # Generating working df
        data = db_testdata_write
        acteur_type_ids = [data["at2"].id, data["at3"].id, data["at4"].id]
        fields = ["identifiant_unique", "statut", "latitude"]
        return cluster_acteurs_read_parents(
            acteur_type_ids=acteur_type_ids,
            fields=fields,
        )

    def test_df_columns(self, df_working):
        assert sorted(df_working.columns.tolist()) == sorted(
            [
                "identifiant_unique",
                "statut",
                "latitude",
                "nom",
                "source_codes",
            ]
        )

    def test_parents_are_valid(self, df_working, db_testdata_write):
        # We should only have parents matching criteria
        data = db_testdata_write
        assert sorted(df_working["identifiant_unique"].tolist()) == sorted(
            [
                data["id_at2_parent_a"],
                data["id_at2_parent_b"],
                data["id_at4_parent"],
            ]
        )

    def test_parents_not_actif_excluded(self, df_working, db_testdata_write):
        # In particular we shouldn't get inactive parents
        assert (
            db_testdata_write["id_at4_parent_inactif"]
            not in df_working["identifiant_unique"].tolist()
        )

    def test_with_regex(self, db_testdata_write):
        # Similar test but this time with a regex filter
        # We should that regex are applied on normalised data
        # but the returned data is original
        data = db_testdata_write
        acteur_type_ids = [data["at2"].id, data["at3"].id, data["at4"].id]
        fields = ["identifiant_unique", "statut", "latitude"]
        df = cluster_acteurs_read_parents(
            acteur_type_ids=acteur_type_ids,
            fields=fields,
            include_only_if_regex_matches_nom=r"parent at(?:1|2) (?:a|b)",
        )
        assert sorted(df["nom"].tolist()) == sorted(
            [
                "Mon parent at2 a",
                "Mon PÂRËNT at2 b",
            ]
        )
