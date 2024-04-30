import pytest

from qfdmo.models import ActeurService, CodeAsNaturalKeyModel
from unit_tests.qfdmo.acteur_factory import ActeurServiceFactory


class TestEntiteServiceNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in ActeurService.mro()

    def test_str(self):
        acteur_service = ActeurServiceFactory.build(
            code="My Code", libelle="My Libelle"
        )
        assert str(acteur_service) == "My Libelle (My Code)"

    @pytest.mark.django_db
    def test_serialize(self):
        acteur_service = ActeurService.objects.create(code="Test Object")
        assert acteur_service.serialize() == {
            "id": acteur_service.id,
            "code": "Test Object",
            "libelle": None,
        }
