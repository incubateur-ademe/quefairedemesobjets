import pytest
from django.core.exceptions import ValidationError

from qfdmo.models import ActeurType, CodeAsNaturalKeyModel


class TestEntiteTypeNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in ActeurType.mro()

    @pytest.mark.parametrize("code", ["ESS", "Ess", "e s s"])
    def test_code_raise_on_bad_code(self, code):
        with pytest.raises(ValidationError):
            acteur_type = ActeurType(code=code, libelle="ESS")
            acteur_type.clean_fields()

    @pytest.mark.parametrize("code", ["ess", "e_s_s", "_ess_"])
    def test_code_good_code(self, code):
        acteur_type = ActeurType(code=code, libelle="ESS")
        assert acteur_type.clean_fields() is None
