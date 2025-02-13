"""
Test file for the ChangeActeurUpdateParentId model.

"""

import pytest

from data.models.change_models import ChangeActeurUpdateParentId
from qfdmo.models import Acteur, RevisionActeur
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory


@pytest.mark.django_db
class TestChangeActeurUpdateParentId:
    def test_model_name(self):
        assert ChangeActeurUpdateParentId.name() == "acteur_update_parent_id"

    def test_raise_if_not_in_base(self):
        # If acteur doesn't exist in base, we should raise an error
        with pytest.raises(Acteur.DoesNotExist):
            ChangeActeurUpdateParentId(identifiant_unique="not found").validate()

    def test_raise_if_parent_not_in_revision(self):
        # If parent doesn't exist in revision, we should raise an error
        ActeurFactory(identifiant_unique="child1")
        data = {"parent_id": "parent1"}
        change = ChangeActeurUpdateParentId(identifiant_unique="child1", data=data)
        with pytest.raises(RevisionActeur.DoesNotExist):
            change.validate()

    def test_created_in_revision_if_not_there(self):
        # Acteur should be updated in revision if not there
        ActeurFactory(identifiant_unique="child2")
        RevisionActeurFactory(identifiant_unique="parent2")
        data = {"parent_id": "parent2"}
        change = ChangeActeurUpdateParentId(identifiant_unique="child2", data=data)
        change.apply()

        rev = RevisionActeur.objects.get(pk="child2")
        assert rev.parent.identifiant_unique == "parent2"

    def test_not_duplicated_in_revision_if_there(self):
        # Acteur should not be duplicated in revision if already there
        # and its parent id should be changed to the new one
        ActeurFactory(identifiant_unique="child3")
        old = RevisionActeurFactory(identifiant_unique="old")
        RevisionActeurFactory(identifiant_unique="parent3")
        RevisionActeurFactory(identifiant_unique="child3", parent=old)
        data = {"parent_id": "parent3"}
        change = ChangeActeurUpdateParentId(identifiant_unique="child3", data=data)
        change.apply()

        rev = RevisionActeur.objects.get(pk="child3")
        assert rev.parent.identifiant_unique == "parent3"
