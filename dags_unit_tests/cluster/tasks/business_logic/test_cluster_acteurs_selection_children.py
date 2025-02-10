import pytest

from dags.cluster.tasks.business_logic import cluster_acteurs_selection_children
from unit_tests.qfdmo.acteur_factory import RevisionActeurFactory


@pytest.mark.django_db
class TestClusterActeursSelectionChildren:

    @pytest.fixture
    def db_testdata_write(self):
        p1 = RevisionActeurFactory(nom="Parent 1", statut="ACTIF")
        p2 = RevisionActeurFactory(nom="Parent 2", statut="ACTIF")
        # 🔴 Pas sélectionné car pas de parent
        RevisionActeurFactory(nom="Orphelin 1", statut="ACTIF")

        # 🟢 Sélectionné car actif + parent
        RevisionActeurFactory(nom="Enfant p1 a", parent=p1, statut="ACTIF")
        # 🔴 Pas sélectionné car inactif
        RevisionActeurFactory(nom="INACTIF p1 b", parent=p1, statut="INACTIF")
        # 🟢 Sélectionné car actif + parent
        RevisionActeurFactory(nom="Enfant p2 a", parent=p2, statut="ACTIF")
        # 🟢 Sélectionné car actif + parent
        RevisionActeurFactory(nom="Enfant p2 b", parent=p2, statut="ACTIF")
        # 🔴 Pas sélectionné car pas de parent
        RevisionActeurFactory(nom="AUTRE", statut="ACTIF")
        return p1, p2

    def test_selection_children(self, db_testdata_write):
        p1, p2 = db_testdata_write
        parent_ids = [p1.identifiant_unique, p2.identifiant_unique]
        fields_to_include = ["nom", "parent", "nombre_enfants", "source_id"]
        df = cluster_acteurs_selection_children(parent_ids, fields_to_include)
        assert df.shape == (3, 4)
        assert df["nom"].tolist() == ["Enfant p1 a", "Enfant p2 a", "Enfant p2 b"]
        assert df.columns.tolist() == fields_to_include
