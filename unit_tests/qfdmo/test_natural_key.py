"""
We will use Acteur model to test NomAsNaturalKeyModel because we need a model in DB
"""

import pytest

from qfdmo.models import Acteur
from unit_tests.qfdmo.acteur_factory import ActeurFactory


class TestActionStr:
    def test_str_blank(self):
        assert ActeurFactory.build(nom="").__str__() == ""

    def test_str_specialchar(self):
        assert ActeurFactory.build(nom="Åctïôn").__str__() == "Åctïôn"


class TestActionNaturalKey:
    def test_natural_key(self):
        assert ActeurFactory.build(nom="Natural key").natural_key() == ("Natural key",)

    @pytest.mark.django_db()
    def test_get_natural_key(self):
        ActeurFactory(nom="Natural key")
        assert (
            Acteur.objects.get_by_natural_key("Natural key").__str__() == "Natural key"
        )
