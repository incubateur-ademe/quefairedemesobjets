import pytest
from enrich.tasks.business_logic.db_read_acteur_cp import (
    db_read_acteur_cp,
    db_read_revision_acteur_cp,
)

from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory


class TestDbReadActeurCp:
    @pytest.fixture(autouse=True)
    def acteurs(self):
        ActeurFactory(identifiant_unique="0", code_postal="01234")
        ActeurFactory(identifiant_unique="1", code_postal="12345")
        ActeurFactory(identifiant_unique="2", code_postal="123456")
        ActeurFactory(identifiant_unique="3", code_postal="1234")
        ActeurFactory(identifiant_unique="4", code_postal="1234567")
        ActeurFactory(identifiant_unique="5", code_postal="12345678")
        ActeurFactory(identifiant_unique="6", code_postal="123.5")
        ActeurFactory(identifiant_unique="7", code_postal="123 5")
        ActeurFactory(identifiant_unique="8", code_postal="")

    @pytest.fixture(autouse=True)
    def revision_acteurs(self):
        RevisionActeurFactory(identifiant_unique="1", code_postal="01234")
        RevisionActeurFactory(identifiant_unique="2", code_postal="12345")
        RevisionActeurFactory(identifiant_unique="3", code_postal="")
        RevisionActeurFactory(identifiant_unique="4", code_postal="1")

    @pytest.mark.django_db()
    def test_db_read_acteur_cp(self):
        df = db_read_acteur_cp()
        assert set(df.columns.tolist()) == {"identifiant_unique", "code_postal"}
        assert set(df["identifiant_unique"].tolist()) == {"2", "3", "4", "5", "6", "7"}

    @pytest.mark.django_db()
    def test_db_read_revision_acteur_cp(self):
        df = db_read_revision_acteur_cp()
        assert set(df.columns.tolist()) == {"identifiant_unique", "code_postal"}
        assert set(df["identifiant_unique"].tolist()) == {"4"}
