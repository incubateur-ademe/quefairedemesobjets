"""
Test file for the ChangeActeurCreateAsParent model.

"""

import pytest

from data.models.changes import ChangeActeurCreateAsParent
from qfdmo.models import Acteur, ActeurType, Action, DisplayedActeur, RevisionActeur


@pytest.mark.django_db
class TestChangeActeurCreateAsParent:
    def test_model_name(self):
        assert ChangeActeurCreateAsParent.name() == "acteur_create_as_parent"

    def test_raise_if_existing(self):
        RevisionActeur(identifiant_unique="p1").save_as_parent()
        change = ChangeActeurCreateAsParent(id="p1")
        with pytest.raises(ValueError, match="Parent to create 'p1' already exists"):
            change.apply()  # calling apply to ensure it calls validate

    @pytest.fixture
    def change_applied(self):
        id = "p2"
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
        change = ChangeActeurCreateAsParent(id=id, data=data)
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
