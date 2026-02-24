import pytest
from cluster.tasks.business_logic.cluster_acteurs_read.children import (
    cluster_acteurs_read_children,
)

from unit_tests.qfdmo.acteur_factory import VueActeurFactory


@pytest.mark.django_db
class TestClusterActeursSelectionChildren:

    @pytest.fixture
    def db_testdata_write(self):
        p1 = VueActeurFactory(nom="Parent 1", statut="ACTIF")
        p2 = VueActeurFactory(nom="Parent 2", statut="ACTIF")
        # 🔴 Pas sélectionné car pas de parent
        VueActeurFactory(nom="Orphelin 1", statut="ACTIF")

        # 🟢 Sélectionné car actif + parent
        VueActeurFactory(nom="Enfant p1 a", parent=p1, statut="ACTIF")
        # 🔴 Pas sélectionné car inactif
        VueActeurFactory(nom="INACTIF p1 b", parent=p1, statut="INACTIF")
        # 🟢 Sélectionné car actif + parent
        VueActeurFactory(nom="Enfant p2 a", parent=p2, statut="ACTIF")
        # 🟢 Sélectionné car actif + parent
        VueActeurFactory(nom="Enfant p2 b", parent=p2, statut="ACTIF")
        # 🔴 Pas sélectionné car pas de parent
        VueActeurFactory(nom="AUTRE", statut="ACTIF")
        return p1, p2

    def test_selection_children(self, db_testdata_write):
        p1, p2 = db_testdata_write
        parent_ids = [p1.identifiant_unique, p2.identifiant_unique]
        fields_to_include = ["nom", "parent", "nombre_enfants", "source_id"]
        df = cluster_acteurs_read_children(parent_ids, fields_to_include)
        assert set(df["nom"].tolist()) == {"Enfant p1 a", "Enfant p2 a", "Enfant p2 b"}
        assert df.columns.tolist() == fields_to_include
