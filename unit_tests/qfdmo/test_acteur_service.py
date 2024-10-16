import pytest
from django.core.exceptions import ValidationError

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

    @pytest.mark.parametrize("code", ["ESS", "Ess", "e s s"])
    def test_code_raise_on_bad_code(self, code):
        with pytest.raises(ValidationError):
            acteur_type = ActeurService(code=code, libelle="ESS")
            acteur_type.clean_fields()

    @pytest.mark.parametrize("code", ["ess", "e_s_s", "_ess_"])
    def test_code_good_code(self, code):
        acteur_type = ActeurService(code=code, libelle="ESS")
        assert acteur_type.clean_fields() is None
