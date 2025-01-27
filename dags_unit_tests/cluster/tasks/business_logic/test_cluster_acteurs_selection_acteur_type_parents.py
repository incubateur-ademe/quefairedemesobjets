"""
Fichier de test pour la fonction cluster_acteurs_selection_acteur_type_parents
"""

import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_selection_acteur_type_parents import (
    cluster_acteurs_selection_acteur_type_parents,
)

from qfdmo.models import DisplayedActeur
from unit_tests.qfdmo.acteur_factory import ActeurTypeFactory, SourceFactory


@pytest.mark.django_db()
class TestClusterActeursSelectionActeurTypeParents:

    @pytest.fixture
    def db_testdata_write(self) -> dict:
        """Création des donnéees de test en DB"""
        data = {}
        data["at1"] = ActeurTypeFactory(code="at1")
        data["at2"] = ActeurTypeFactory(code="at2")
        data["at3"] = ActeurTypeFactory(code="at3")
        data["at4"] = ActeurTypeFactory(code="at4")
        data["s1"] = SourceFactory(code="s1")
        data["id_at1_parent"] = "10000000-0000-0000-0000-000000000000"
        # On fait exprès d'utiliser des UUIDs partout, y compris
        # pour les non-parents, pour démontrer que la requête ne
        # se base pas sur l'anatomie des IDs
        data["id_at2_pas_parent"] = "10000000-0000-0000-0000-000000000000"
        data["id_at2_parent_a"] = "20000000-0000-0000-0000-00000000000a"
        data["id_at2_parent_b"] = "20000000-0000-0000-0000-00000000000b"
        data["id_at3_pas_parent"] = "30000000-0000-0000-0000-000000000000"
        data["id_at4_parent"] = "40000000-0000-0000-0000-000000000000"

        # at1
        # Parent MAIS d'un acteur type non sélectionné (at1)
        DisplayedActeur.objects.create(
            acteur_type=data["at1"],
            identifiant_unique=data["id_at1_parent"],
        )
        # at2
        # On test le cas où il y a plusieurs parents
        # Pas parent car avec une source
        DisplayedActeur.objects.create(
            acteur_type=data["at2"],
            identifiant_unique=data["id_at2_pas_parent"],
            source=data["s1"],
        )
        # Parents car sans source
        DisplayedActeur.objects.create(
            acteur_type=data["at2"],
            identifiant_unique=data["id_at2_parent_a"],
        )
        DisplayedActeur.objects.create(
            acteur_type=data["at2"],
            identifiant_unique=data["id_at2_parent_b"],
        )
        # at3
        # Pour at3 on test le cas où il n'y a pas de parent
        DisplayedActeur.objects.create(
            acteur_type=data["at3"],
            identifiant_unique=data["id_at3_pas_parent"],
            source=data["s1"],
        )
        # at4
        # On test le cas où il y a 1 parent
        DisplayedActeur.objects.create(
            acteur_type=data["at4"],
            identifiant_unique=data["id_at4_parent"],
        )

        return data

    @pytest.fixture
    def df(self, db_testdata_write) -> pd.DataFrame:
        """On génère et retourne la df pour les tests"""
        data = db_testdata_write
        acteur_type_ids = [data["at2"].id, data["at3"].id, data["at4"].id]
        fields = ["identifiant_unique", "statut", "latitude"]
        return cluster_acteurs_selection_acteur_type_parents(
            acteur_type_ids=acteur_type_ids,
            fields=fields,
        )

    def test_df_shape(self, df):
        # 3 parents (2 parents pour at2 + 0 pour at3 + 1 pour at4)
        # 3 champs
        assert df.shape == (3, 3)

    def test_df_columns(self, df):
        # Seules les colonnes demandées sont retournées
        assert df.columns.tolist() == ["identifiant_unique", "statut", "latitude"]

    def test_parents_are_valid(self, df, db_testdata_write):
        # Seuls les parents des acteurs types demandés
        # sont retournés
        data = db_testdata_write
        assert sorted(df["identifiant_unique"].tolist()) == sorted(
            [
                data["id_at2_parent_a"],
                data["id_at2_parent_b"],
                data["id_at4_parent"],
            ]
        )
