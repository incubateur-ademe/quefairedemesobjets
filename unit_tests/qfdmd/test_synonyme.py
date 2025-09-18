import pytest

from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory


class TestSynonyme:
    @pytest.mark.django_db
    def test_str(self):
        synonyme = SynonymeFactory(nom="Nom du synonyme")
        assert str(synonyme) == "Nom du synonyme"
        assert synonyme.slug == "nom-du-synonyme"

    @pytest.mark.django_db
    def test_slug_max_length(self):
        produit = ProduitFactory(nom="Produit")
        synonyme255 = SynonymeFactory(nom="X" * 255, produit=produit)
        assert synonyme255.slug == "x" * 255

        synonyme256 = SynonymeFactory(nom="Y" * 256, produit=produit)
        assert synonyme256.slug == "y" * 255
