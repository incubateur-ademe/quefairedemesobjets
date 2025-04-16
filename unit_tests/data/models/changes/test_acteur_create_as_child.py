import pytest
from django.contrib.gis.geos import Point

from data.models.changes.acteur_create_as_child import ChangeActeurCreateAsChild
from qfdmo.models import Acteur, RevisionActeur
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurTypeFactory,
    SourceFactory,
)


@pytest.mark.django_db
class TestChangeActeurCreateAsChild:
    @pytest.mark.parametrize(
        "data,missing",
        [({"parent": "456"}, "parent_reason"), ({"parent_reason": "test"}, "parent")],
    )
    def test_raise_if_missing_params(self, data, missing):
        change = ChangeActeurCreateAsChild(id="123", data=data)
        with pytest.raises(ValueError, match=f"champ '{missing}' à renseigner"):
            change.apply()

    def test_raise_if_acteur_exists(self):
        ActeurFactory(identifiant_unique="123")
        change = ChangeActeurCreateAsChild(
            id="123", data={"parent": "456", "parent_reason": "test"}
        )
        with pytest.raises(ValueError, match="existe déjà"):
            change.apply()

    def test_working(self):
        # Create parent
        source = SourceFactory(code="source1")
        atype = ActeurTypeFactory(code="atype1")
        parent = RevisionActeur.objects.create(
            identifiant_unique="parent1",
            source=source,
            acteur_type=atype,
            statut="ACTIF",
            location=Point(1, 1),
        )
        # Create child
        change = ChangeActeurCreateAsChild(
            id="child1",
            data={
                "nom": "my child1",
                "source": source,
                "acteur_type": atype,
                "statut": "ACFIF",
                "location": Point(1, 1),
                "parent": parent,
                "parent_reason": "test",
            },
        )
        change.apply()

        # Acteur created in base to hold the core data
        base = Acteur.objects.get(pk="child1")
        assert base.identifiant_unique == "child1"
        assert base.nom == "my child1"
        assert base.source.pk == source.pk
        assert base.acteur_type.pk == atype.pk
        assert base.statut == "ACFIF"
        assert base.location.x == 1
        assert base.location.y == 1

        # Acteur created in revision to hold the parent reference
        revision = RevisionActeur.objects.get(pk="child1")
        assert revision.parent.pk == parent.pk
        assert revision.parent_reason == "test"
        assert not revision.nom
