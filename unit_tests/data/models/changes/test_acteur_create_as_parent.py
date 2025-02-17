"""
Test file for the ChangeActeurCreateAsParent model.

"""

import pytest

from data.models.changes import ChangeActeurCreateAsParent
from qfdmo.models import Acteur, DisplayedActeur, RevisionActeur


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
        data = {"nom": "foo", "ville": "bar"}
        data.update({"longitude": 1, "latitude": 2})
        change = ChangeActeurCreateAsParent(id=id, data=data)
        change.apply()
        return id

    def test_apply_created_with_data_in_revision(self, change_applied):
        id = change_applied
        rev = RevisionActeur.objects.get(pk=id)
        assert rev.nom == "foo"
        assert rev.ville == "bar"
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
