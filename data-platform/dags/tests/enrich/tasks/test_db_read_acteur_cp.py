import pytest
from enrich.tasks.business_logic.db_read_acteur_cp import (
    db_read_acteur_cp,
    db_read_revision_acteur_cp,
)

from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory


class TestDbReadActeurCp:
    @pytest.fixture(autouse=True)
    def acteurs(self):
        ActeurFactory(
            identifiant_unique="valid-cp-with-prefix-zero", code_postal="01234"
        )
        ActeurFactory(identifiant_unique="valid-cp", code_postal="12345")
        ActeurFactory(identifiant_unique="invalid-6-characters", code_postal="123456")
        ActeurFactory(identifiant_unique="invalid-4-characters", code_postal="1234")
        ActeurFactory(
            identifiant_unique="invalid-7-characters-override-1-characters",
            code_postal="1234567",
        )
        ActeurFactory(identifiant_unique="invalid-8-characters", code_postal="12345678")
        ActeurFactory(identifiant_unique="invalid-decimal", code_postal="123.5")
        ActeurFactory(identifiant_unique="invalid-space", code_postal="123 5")
        ActeurFactory(identifiant_unique="empty", code_postal="")

    @pytest.fixture(autouse=True)
    def revision_acteurs(self):
        RevisionActeurFactory(identifiant_unique="valid-cp", code_postal="01234")
        RevisionActeurFactory(
            identifiant_unique="invalid-6-characters", code_postal="12345"
        )
        RevisionActeurFactory(identifiant_unique="invalid-4-characters", code_postal="")
        RevisionActeurFactory(
            identifiant_unique="invalid-7-characters-override-1-characters",
            code_postal="1",
        )

    @pytest.mark.django_db()
    def test_db_read_acteur_cp(self):
        df = db_read_acteur_cp()
        assert set(df.columns.tolist()) == {"identifiant_unique", "code_postal"}
        assert set(df["identifiant_unique"].tolist()) == {
            "invalid-6-characters",
            "invalid-4-characters",
            "invalid-7-characters-override-1-characters",
            "invalid-8-characters",
            "invalid-decimal",
            "invalid-space",
        }

    @pytest.mark.django_db()
    def test_db_read_revision_acteur_cp(self):
        df = db_read_revision_acteur_cp()
        assert set(df.columns.tolist()) == {"identifiant_unique", "code_postal"}
        assert set(df["identifiant_unique"].tolist()) == {
            "invalid-7-characters-override-1-characters"
        }
