import pytest

from qfdmo.models import ActeurType, NomAsNaturalKeyModel
from unit_tests.qfdmo.acteur_factory import ActeurTypeFactory


class TestEntiteTypeNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in ActeurType.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        acteur_type = ActeurTypeFactory.build(
            nom="Test Object",
            nom_affiche="Test Object Affiche",
            lvao_id=123,
        )
        assert acteur_type.serialize() == {
            "id": acteur_type.id,
            "nom": "Test Object",
            "nom_affiche": "Test Object Affiche",
            "lvao_id": 123,
        }
