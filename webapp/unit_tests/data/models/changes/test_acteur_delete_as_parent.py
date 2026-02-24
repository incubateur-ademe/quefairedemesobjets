"""
Test file for ChangeActeurDeleteAsParent model
which depends on the other models to simulate
overall acteur management to verify that parent
deletion is automatic when all children have been
updated to point to a new parent.

"""

import pytest

from data.models.changes import (
    ChangeActeurCreateAsParent,
    ChangeActeurDeleteAsParent,
    ChangeActeurUpdateParentId,
)
from qfdmo.models import RevisionActeur
from qfdmo.models.acteur import ActeurStatus
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory


@pytest.mark.django_db
class TestChangeActeurDeleteAsParent:
    def test_model_name(self):
        assert ChangeActeurDeleteAsParent.name() == "acteur_delete_as_parent"

    def test_raise_if_present_with_actif_children(self):
        # We expect acteur management to automatically delete parent for us
        p1 = RevisionActeurFactory(identifiant_unique="p1")
        RevisionActeurFactory(identifiant_unique="e1", parent=p1)
        RevisionActeurFactory(
            identifiant_unique="e2", parent=p1, statut=ActeurStatus.INACTIF
        )
        RevisionActeurFactory(
            identifiant_unique="e3", parent=p1, statut=ActeurStatus.SUPPRIME
        )
        change = ChangeActeurDeleteAsParent(id="p1")
        with pytest.raises(ValueError, match="Parent 'p1' should already be deleted"):
            change.apply()  # calling apply to ensure it calls validate

    def test_deleted_if_present_with_children(self):
        # We expect acteur management to automatically delete parent for us
        p1 = RevisionActeurFactory(identifiant_unique="p1")
        e2 = RevisionActeurFactory(
            identifiant_unique="e2", parent=p1, statut=ActeurStatus.INACTIF
        )
        e3 = RevisionActeurFactory(
            identifiant_unique="e3", parent=p1, statut=ActeurStatus.SUPPRIME
        )
        change = ChangeActeurDeleteAsParent(id="p1")
        change.apply()

        p1 = RevisionActeur.objects.filter(pk="p1").first()
        e2.refresh_from_db()
        e3.refresh_from_db()

        assert p1 is None
        assert e2.parent is None
        assert e3.parent is None

    def test_ensure_deletion_is_automatic(self):
        # We replay the e2e scenario of having children pointing
        # to some parent, and that parent being automatically deleted
        # when all children have been updated to point to a new parent

        # Create 1 parent and 2 children pointing to it
        ChangeActeurCreateAsParent(id="p1").apply()
        ActeurFactory(identifiant_unique="a1")
        ActeurFactory(identifiant_unique="a2")
        data = {"parent_id": "p1"}
        ChangeActeurUpdateParentId(id="a1", data=data).apply()
        ChangeActeurUpdateParentId(id="a2", data=data).apply()

        # At this point the parent should exist
        assert RevisionActeur.objects.get(pk="p1")

        # We create a new parent and update 1 child to point to it
        ChangeActeurCreateAsParent(id="p2").apply()
        data = {"parent_id": "p2"}
        ChangeActeurUpdateParentId(id="a1", data=data).apply()

        # The 1st parent should still exists as it still has 1 child
        assert RevisionActeur.objects.get(pk="p1")

        # We update the 2nd child to point to the new parent
        ChangeActeurUpdateParentId(id="a2", data=data).apply()

        # The 1st parent should have been automatically deleted
        assert not RevisionActeur.objects.filter(pk="p1").exists()

        # And finally the model should pass
        ChangeActeurDeleteAsParent(id="p1").apply()
