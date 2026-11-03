import pytest

from unit_tests.assistant.helpers import action_of
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory


@pytest.fixture
def fiche():
    """A live fiche: the views only look up `live()` pages."""
    return ProduitPageFactory(parent=None)


@pytest.fixture
def reparer():
    """The `reparer` Action, in its `reparer` GroupeAction."""
    return action_of("reparer", libelle_court="Réparer", couleur="#009081")
