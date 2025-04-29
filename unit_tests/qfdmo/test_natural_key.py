"""
We will use Produit model to test NomAsNaturalKeyModel because we need a model in DB
"""

import pytest

from qfdmd.models import Produit
from unit_tests.qfdmd.qfdmod_factory import ProduitFactory


class TestActionNaturalKey:
    def test_natural_key(self):
        assert ProduitFactory.build(nom="Natural key").natural_key() == ("Natural key",)

    @pytest.mark.django_db()
    def test_get_natural_key(self):
        produit = ProduitFactory(nom="Natural key")
        assert Produit.objects.get_by_natural_key("Natural key") is not None
        assert Produit.objects.get_by_natural_key("Natural key").pk == produit.pk
