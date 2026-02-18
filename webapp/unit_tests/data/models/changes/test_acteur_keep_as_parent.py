"""
Test file for the ChangeActeurKeepAsParent model.

"""

import pytest

from data.models.changes import ChangeActeurKeepAsParent
from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import Acteur, ActeurType, Action, DisplayedActeur, RevisionActeur


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
        id = "parent_created"
        RevisionActeur(identifiant_unique=id).save_as_parent()
        at = ActeurType(code="my_at")
        action = Action(code="my_action")
        at.save()
        action.save()
        data = {
            "nom": "foo",
            "ville": "bar",
            "longitude": 1,
            "latitude": 2,
            "acteur_type": at.pk,
            "action_principale": action.pk,
        }
        change = ChangeActeurKeepAsParent(id=id, data=data)
        change.apply()
        return id, at, action

    def test_apply_created_with_data_in_revision(self, change_applied):
        id, at, action = change_applied
        rev = RevisionActeur.objects.get(pk=id)
        assert rev.nom == "foo"
        assert rev.ville == "bar"
        assert rev.location.x == 1
        assert rev.location.y == 2
        assert rev.acteur_type.pk == at.pk
        assert rev.action_principale.pk == action.pk

    def test_apply_doesnt_create_in_base(self, change_applied):
        id = change_applied
        assert not Acteur.objects.filter(pk=id).exists()

    def test_apply_doesnt_create_in_displayed(self, change_applied):
        id = change_applied
        assert not DisplayedActeur.objects.filter(pk=id).exists()
