"""
Test file for the ChangeActeurKeepAsParent model.

"""

from data.models.change_models import (
    ChangeActeurKeepAsParent,
    ChangeActeurNothingRevision,
)


class TestChangeActeurKeepAsParent:
    def test_model_name(self):
        assert ChangeActeurKeepAsParent.name() == "acteur_keep_as_parent"

    def test_inherits_from_change_acteur_change_nothing_in_revision(self):
        assert issubclass(ChangeActeurKeepAsParent, ChangeActeurNothingRevision)
