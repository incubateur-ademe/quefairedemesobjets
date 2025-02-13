"""
Test file for the ChangeActeurCreateAsParent model.

"""

import pytest

from data.models.change_models import ChangeActeurCreateAsParent
from qfdmo.models import Acteur, RevisionActeur
from unit_tests.qfdmo.acteur_factory import RevisionActeurFactory


@pytest.mark.django_db
class TestChangeActeurCreateAsParent:
    def test_model_name(self):
        assert ChangeActeurCreateAsParent.name() == "acteur_create_as_parent"

    def test_raise_if_existing(self):
        RevisionActeurFactory(identifiant_unique="p1")
        change = ChangeActeurCreateAsParent(identifiant_unique="p1")
        with pytest.raises(ValueError, match="Parent to create 'p1' already exists"):
            change.apply()  # calling apply to ensure it calls validate

    def test_apply_created_in_revision_but_not_base(self):
        change = ChangeActeurCreateAsParent(identifiant_unique="p3")
        change.apply()

        assert RevisionActeur.objects.get(pk="p3")
        assert not Acteur.objects.filter(pk="p3").exists()
