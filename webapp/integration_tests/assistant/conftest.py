import pytest

from unit_tests.qfdmo.carte_config_factory import CarteConfigFactory


@pytest.fixture(autouse=True)
def legacy_produit_carte_config(db):
    """Carte embarquée sur les fiches legacy (slug product par défaut)."""
    return CarteConfigFactory(slug="product", nom="Product")
