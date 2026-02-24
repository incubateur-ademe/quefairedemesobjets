from unit_tests.qfdmd.qfdmod_factory import ProduitFactory


class TestProduit:
    def test_str(self):
        produit = ProduitFactory.build(nom="Nom du produit", id=1)
        assert str(produit) == "1 - Nom du produit"
