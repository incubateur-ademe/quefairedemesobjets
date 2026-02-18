"""
Test file for the ChangeActeurVerifyRevision model.

Such model might seem unnecessary at first,
but read its file's docstring to understand why it is useful.

"""

import pytest

from data.models.changes import ChangeActeurVerifyRevision
from qfdmo.models import RevisionActeur
from unit_tests.qfdmo.acteur_factory import RevisionActeurFactory


@pytest.mark.django_db
class TestChangeActeurVerifyRevision:
    def test_model_name(self):
        assert ChangeActeurVerifyRevision.name() == "acteur_verify_presence_in_revision"

    def test_raise_if_data_present(self):
        RevisionActeurFactory(identifiant_unique="acteur1")
        change = ChangeActeurVerifyRevision(id="acteur1", data={"foo": "bar"})
        with pytest.raises(ValueError, match="No data expected"):
            change.apply()  # calling apply to ensure it calls validate

    def test_raise_if_acteur_not_in_base(self):
        change = ChangeActeurVerifyRevision(id="acteur2")
        with pytest.raises(RevisionActeur.DoesNotExist):
            change.apply()

    def test_pass_nothing_done(self):
        RevisionActeurFactory(identifiant_unique="acteur3")
        change = ChangeActeurVerifyRevision(id="acteur3")
        change.apply()
