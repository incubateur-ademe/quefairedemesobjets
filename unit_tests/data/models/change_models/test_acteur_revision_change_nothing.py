"""
Test file for the ChangeActeurNothingRevision model.

Such model might seem unnecessary at first,
but read its file's docstring to understand why it is useful.

"""

import pytest

from data.models.change_models import ChangeActeurNothingRevision
from qfdmo.models import RevisionActeur
from unit_tests.qfdmo.acteur_factory import RevisionActeurFactory


@pytest.mark.django_db
class TestChangeActeurNothingRevision:
    def test_model_name(self):
        assert ChangeActeurNothingRevision.name() == "acteur_change_nothing_in_revision"

    def test_raise_if_data_present(self):
        RevisionActeurFactory(identifiant_unique="acteur1")
        change = ChangeActeurNothingRevision(
            identifiant_unique="acteur1", data={"foo": "bar"}
        )
        with pytest.raises(ValueError, match="No data expected"):
            change.apply()  # calling apply to ensure it calls validate

    def test_raise_if_acteur_not_in_base(self):
        change = ChangeActeurNothingRevision(identifiant_unique="acteur2")
        with pytest.raises(RevisionActeur.DoesNotExist):
            change.apply()

    def test_pass_nothing_done(self):
        RevisionActeurFactory(identifiant_unique="acteur3")
        change = ChangeActeurNothingRevision(identifiant_unique="acteur3")
        change.apply()
