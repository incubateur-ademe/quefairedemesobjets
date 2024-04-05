import pytest

from qfdmo.models import ActeurType, CodeAsNaturalKeyModel
from unit_tests.qfdmo.acteur_factory import ActeurTypeFactory


class TestEntiteTypeNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in ActeurType.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        acteur_type = ActeurTypeFactory.build(
            code="Test Object",
            libelle="Test Object Affiche",
        )
        assert acteur_type.serialize() == {
            "id": acteur_type.id,
            "code": "Test Object",
            "libelle": "Test Object Affiche",
        }
