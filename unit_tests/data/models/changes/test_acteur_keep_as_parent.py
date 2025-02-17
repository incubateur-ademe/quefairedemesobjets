"""
Test file for the ChangeActeurKeepAsParent model.

"""

from datetime import datetime

import pytest

from data.models.changes import ChangeActeurKeepAsParent
from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import Acteur, DisplayedActeur, RevisionActeur


@pytest.mark.django_db
class TestChangeActeurKeepAsParent:
    def test_model_name(self):
        assert ChangeActeurKeepAsParent.name() == "acteur_keep_as_parent"

    def test_inherits_from_change_acteur_verify_presence_in_revision(self):
        assert issubclass(ChangeActeurKeepAsParent, ChangeActeurAbstract)

    def test_raise_if_parent_does_not_exist(self):
        with pytest.raises(RevisionActeur.DoesNotExist):
            ChangeActeurKeepAsParent(id="p1").apply()

    @pytest.fixture
    def change_applied(self):
        now = datetime.now().isoformat()
        id = f"parent_created {now}"
        RevisionActeur(identifiant_unique=id).save_as_parent()
        data = {"nom": "AFTER"}
        data.update({"longitude": 1, "latitude": 2})
        ChangeActeurKeepAsParent(id=id, data=data).apply()
        return id

    def test_apply_properly_updates_parent(self, change_applied):
        id = change_applied
        rev = RevisionActeur.objects.get(pk=id)
        assert rev.nom == "AFTER"
        assert rev.location.x == 1
        assert rev.location.y == 2
        assert "longitude" not in rev.location
        assert "latitude" not in rev.location

    def test_apply_doesnt_create_in_base(self, change_applied):
        id = change_applied
        assert not Acteur.objects.filter(pk=id).exists()

    def test_apply_doesnt_create_in_displayed(self, change_applied):
        id = change_applied
        assert not DisplayedActeur.objects.filter(pk=id).exists()
