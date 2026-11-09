import pytest

from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory


@pytest.fixture
def fiche():
    """A live fiche: the views only look up `live()` pages."""
    return ProduitPageFactory(parent=None)
